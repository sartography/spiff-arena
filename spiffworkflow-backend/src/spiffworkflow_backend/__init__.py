"""__init__."""
import os
from typing import Any

import connexion  # type: ignore
import flask.app
import flask.json
import sqlalchemy
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from flask.json.provider import DefaultJSONProvider
from flask_bpmn.api.api_error import api_error_blueprint
from flask_bpmn.models.db import db
from flask_bpmn.models.db import migrate
from flask_cors import CORS  # type: ignore
from flask_mail import Mail  # type: ignore

import spiffworkflow_backend.load_database_models  # noqa: F401
from spiffworkflow_backend.config import setup_config
from spiffworkflow_backend.routes.admin_blueprint.admin_blueprint import admin_blueprint
from spiffworkflow_backend.routes.process_api_blueprint import process_api_blueprint
from spiffworkflow_backend.routes.user_blueprint import user_blueprint
from spiffworkflow_backend.services.background_processing_service import (
    BackgroundProcessingService,
)


class MyJSONEncoder(DefaultJSONProvider):
    """MyJSONEncoder."""

    def default(self, obj: Any) -> Any:
        """Default."""
        if hasattr(obj, "serialized"):
            return obj.serialized
        elif isinstance(obj, sqlalchemy.engine.row.Row):  # type: ignore
            return_dict = {}
            for row_key in obj.keys():
                row_value = obj[row_key]
                if hasattr(row_value, "__dict__"):
                    return_dict.update(row_value.__dict__)
                else:
                    return_dict.update({row_key: row_value})
            return_dict.pop("_sa_instance_state")
            return return_dict
        return super().default(obj)

    def dumps(self, obj: Any, **kwargs: Any) -> Any:
        """Dumps."""
        kwargs.setdefault("default", self.default)
        return super().dumps(obj, **kwargs)


def start_scheduler(app: flask.app.Flask) -> None:
    """Start_scheduler."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        BackgroundProcessingService(app).process_message_instances_with_app_context,
        "interval",
        seconds=10,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).run,
        "interval",
        seconds=30,
    )
    scheduler.start()


def create_app() -> flask.app.Flask:
    """Create_app."""
    # We need to create the sqlite database in a known location.
    # If we rely on the app.instance_path without setting an environment
    # variable, it will be one thing when we run flask db upgrade in the
    # noxfile and another thing when the tests actually run.
    # instance_path is described more at https://flask.palletsprojects.com/en/2.1.x/config/
    connexion_app = connexion.FlaskApp(
        __name__, server_args={"instance_path": os.environ.get("FLASK_INSTANCE_PATH")}
    )
    app = connexion_app.app
    app.config["CONNEXION_APP"] = connexion_app
    app.config["SESSION_TYPE"] = "filesystem"

    if os.environ.get("FLASK_SESSION_SECRET_KEY") is None:
        raise KeyError(
            "Cannot find the secret_key from the environment. Please set FLASK_SESSION_SECRET_KEY"
        )

    app.secret_key = os.environ.get("FLASK_SESSION_SECRET_KEY")

    setup_config(app)
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(user_blueprint)
    app.register_blueprint(process_api_blueprint)
    app.register_blueprint(api_error_blueprint)
    app.register_blueprint(admin_blueprint, url_prefix="/admin")

    origins_re = [
        r"^https?:\/\/%s(.*)" % o.replace(".", r"\.")
        for o in app.config["CORS_ALLOW_ORIGINS"]
    ]
    CORS(app, origins=origins_re)

    connexion_app.add_api("api.yml", base_path="/v1.0")

    mail = Mail(app)
    app.config["MAIL_APP"] = mail

    app.json = MyJSONEncoder(app)

    if app.config["PROCESS_WAITING_MESSAGES"]:
        start_scheduler(app)

    configure_sentry(app)

    return app  # type: ignore


def get_hacked_up_app_for_script() -> flask.app.Flask:
    """Get_hacked_up_app_for_script."""
    os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "development"
    flask_env_key = "FLASK_SESSION_SECRET_KEY"
    os.environ[flask_env_key] = "whatevs"
    if "BPMN_SPEC_ABSOLUTE_DIR" not in os.environ:
        home = os.environ["HOME"]
        full_process_model_path = (
            f"{home}/projects/github/sartography/sample-process-models"
        )
        if os.path.isdir(full_process_model_path):
            os.environ["BPMN_SPEC_ABSOLUTE_DIR"] = full_process_model_path
        else:
            raise Exception(f"Could not find {full_process_model_path}")
    app = create_app()
    return app


def configure_sentry(app: flask.app.Flask) -> None:
    """Configure_sentry."""
    import sentry_sdk
    from flask import Flask
    from sentry_sdk.integrations.flask import FlaskIntegration

    sentry_sample_rate = app.config.get("SENTRY_SAMPLE_RATE")
    if sentry_sample_rate is None:
        return
    sentry_sdk.init(
        dsn=app.config.get("SENTRY_DSN"),
        integrations=[
            FlaskIntegration(),
        ],
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        # We recommend adjusting this value in production.
        traces_sample_rate=float(sentry_sample_rate),
    )

    app = Flask(__name__)

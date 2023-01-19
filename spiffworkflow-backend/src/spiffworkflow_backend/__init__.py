"""__init__."""
import os
from typing import Any

import connexion  # type: ignore
import flask.app
import flask.json
import sqlalchemy
from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
from apscheduler.schedulers.base import BaseScheduler  # type: ignore
from flask.json.provider import DefaultJSONProvider
from flask_cors import CORS  # type: ignore
from flask_mail import Mail  # type: ignore
from werkzeug.exceptions import NotFound

import spiffworkflow_backend.load_database_models  # noqa: F401
from spiffworkflow_backend.config import setup_config
from spiffworkflow_backend.exceptions.api_error import api_error_blueprint
from spiffworkflow_backend.helpers.api_version import V1_API_PATH_PREFIX
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import migrate
from spiffworkflow_backend.routes.admin_blueprint.admin_blueprint import admin_blueprint
from spiffworkflow_backend.routes.openid_blueprint.openid_blueprint import (
    openid_blueprint,
)
from spiffworkflow_backend.routes.user import set_new_access_token_in_cookie
from spiffworkflow_backend.routes.user import verify_token
from spiffworkflow_backend.routes.user_blueprint import user_blueprint
from spiffworkflow_backend.services.authorization_service import AuthorizationService
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
                if hasattr(row_value, "serialized"):
                    return_dict.update(row_value.serialized)
                elif hasattr(row_value, "__dict__"):
                    return_dict.update(row_value.__dict__)
                else:
                    return_dict.update({row_key: row_value})
            if "_sa_instance_state" in return_dict:
                return_dict.pop("_sa_instance_state")
            return return_dict
        return super().default(obj)

    def dumps(self, obj: Any, **kwargs: Any) -> Any:
        """Dumps."""
        kwargs.setdefault("default", self.default)
        return super().dumps(obj, **kwargs)


def start_scheduler(
    app: flask.app.Flask, scheduler_class: BaseScheduler = BackgroundScheduler
) -> None:
    """Start_scheduler."""
    scheduler = scheduler_class()
    scheduler.add_job(
        BackgroundProcessingService(app).process_message_instances_with_app_context,
        "interval",
        seconds=10,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_waiting_process_instances,
        "interval",
        seconds=10,
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
            "Cannot find the secret_key from the environment. Please set"
            " FLASK_SESSION_SECRET_KEY"
        )

    app.secret_key = os.environ.get("FLASK_SESSION_SECRET_KEY")

    setup_config(app)
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(user_blueprint)
    app.register_blueprint(api_error_blueprint)
    app.register_blueprint(admin_blueprint, url_prefix="/admin")
    app.register_blueprint(openid_blueprint, url_prefix="/openid")

    # preflight options requests will be allowed if they meet the requirements of the url regex.
    # we will add an Access-Control-Max-Age header to the response to tell the browser it doesn't
    # need to continually keep asking for the same path.
    origins_re = [
        r"^https?:\/\/%s(.*)" % o.replace(".", r"\.")
        for o in app.config["CORS_ALLOW_ORIGINS"]
    ]
    CORS(app, origins=origins_re, max_age=3600, supports_credentials=True)

    connexion_app.add_api("api.yml", base_path=V1_API_PATH_PREFIX)

    mail = Mail(app)
    app.config["MAIL_APP"] = mail

    app.json = MyJSONEncoder(app)

    # do not start the scheduler twice in flask debug mode
    if (
        app.config["RUN_BACKGROUND_SCHEDULER"]
        and os.environ.get("WERKZEUG_RUN_MAIN") != "true"
    ):
        start_scheduler(app)

    configure_sentry(app)

    app.before_request(verify_token)
    app.before_request(AuthorizationService.check_for_permission)
    app.after_request(set_new_access_token_in_cookie)

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
    from sentry_sdk.integrations.flask import FlaskIntegration

    # get rid of NotFound errors
    def before_send(event: Any, hint: Any) -> Any:
        """Before_send."""
        if "exc_info" in hint:
            _exc_type, exc_value, _tb = hint["exc_info"]
            # NotFound is mostly from web crawlers
            if isinstance(exc_value, NotFound):
                return None
        return event

    sentry_errors_sample_rate = app.config.get("SENTRY_ERRORS_SAMPLE_RATE")
    if sentry_errors_sample_rate is None:
        raise Exception("SENTRY_ERRORS_SAMPLE_RATE is not set somehow")

    sentry_traces_sample_rate = app.config.get("SENTRY_TRACES_SAMPLE_RATE")
    if sentry_traces_sample_rate is None:
        raise Exception("SENTRY_TRACES_SAMPLE_RATE is not set somehow")

    sentry_sdk.init(
        dsn=app.config.get("SENTRY_DSN"),
        integrations=[
            FlaskIntegration(),
        ],
        environment=app.config["ENV_IDENTIFIER"],
        # sample_rate is the errors sample rate. we usually set it to 1 (100%)
        # so we get all errors in sentry.
        sample_rate=float(sentry_errors_sample_rate),
        # Set traces_sample_rate to capture a certain percentage
        # of transactions for performance monitoring.
        # We recommend adjusting this value to less than 1(00%) in production.
        traces_sample_rate=float(sentry_traces_sample_rate),
        before_send=before_send,
    )

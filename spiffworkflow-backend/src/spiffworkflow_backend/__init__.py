import base64
import faulthandler
import json
import os
import sys
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
from flask_simple_crypt import SimpleCrypt  # type: ignore
from prometheus_flask_exporter import ConnexionPrometheusMetrics  # type: ignore
from werkzeug.exceptions import NotFound

import spiffworkflow_backend.load_database_models  # noqa: F401
from spiffworkflow_backend.config import setup_config
from spiffworkflow_backend.exceptions.api_error import api_error_blueprint
from spiffworkflow_backend.helpers.api_version import V1_API_PATH_PREFIX
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import migrate
from spiffworkflow_backend.routes.openid_blueprint.openid_blueprint import openid_blueprint
from spiffworkflow_backend.routes.user import set_new_access_token_in_cookie
from spiffworkflow_backend.routes.user import verify_token
from spiffworkflow_backend.routes.user_blueprint import user_blueprint
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.background_processing_service import BackgroundProcessingService


class MyJSONEncoder(DefaultJSONProvider):
    def default(self, obj: Any) -> Any:
        if hasattr(obj, "serialized"):
            return obj.serialized()
        elif isinstance(obj, sqlalchemy.engine.row.Row):  # type: ignore
            return_dict = {}
            row_mapping = obj._mapping
            for row_key in row_mapping.keys():
                row_value = row_mapping[row_key]
                if hasattr(row_value, "serialized"):
                    return_dict.update(row_value.serialized())
                elif hasattr(row_value, "__dict__"):
                    return_dict.update(row_value.__dict__)
                else:
                    return_dict.update({row_key: row_value})
            if "_sa_instance_state" in return_dict:
                return_dict.pop("_sa_instance_state")
            return return_dict
        return super().default(obj)

    def dumps(self, obj: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("default", self.default)
        return super().dumps(obj, **kwargs)


def start_scheduler(app: flask.app.Flask, scheduler_class: BaseScheduler = BackgroundScheduler) -> None:
    scheduler = scheduler_class()

    # TODO: polling intervals for messages job
    polling_interval_in_seconds = app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_POLLING_INTERVAL_IN_SECONDS"]
    not_started_polling_interval_in_seconds = app.config[
        "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_NOT_STARTED_POLLING_INTERVAL_IN_SECONDS"
    ]
    user_input_required_polling_interval_in_seconds = app.config[
        "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_USER_INPUT_REQUIRED_POLLING_INTERVAL_IN_SECONDS"
    ]
    # TODO: add job to release locks to simplify other queries
    # TODO: add job to delete completed entires
    # TODO: add job to run old/low priority instances so they do not get drowned out

    scheduler.add_job(
        BackgroundProcessingService(app).process_message_instances_with_app_context,
        "interval",
        seconds=10,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_not_started_process_instances,
        "interval",
        seconds=not_started_polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_waiting_process_instances,
        "interval",
        seconds=polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).process_user_input_required_process_instances,
        "interval",
        seconds=user_input_required_polling_interval_in_seconds,
    )
    scheduler.add_job(
        BackgroundProcessingService(app).remove_stale_locks,
        "interval",
        seconds=app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"],
    )
    scheduler.start()


def should_start_scheduler(app: flask.app.Flask) -> bool:
    if not app.config["SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER_IN_CREATE_APP"]:
        return False

    # do not start the scheduler twice in flask debug mode but support code reloading
    if app.config["ENV_IDENTIFIER"] == "local_development" and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        return False

    return True


class NoOpCipher:
    def encrypt(self, value: str) -> bytes:
        return str.encode(value)

    def decrypt(self, value: str) -> str:
        return value


def create_app() -> flask.app.Flask:
    faulthandler.enable()

    # We need to create the sqlite database in a known location.
    # If we rely on the app.instance_path without setting an environment
    # variable, it will be one thing when we run flask db upgrade in the
    # noxfile and another thing when the tests actually run.
    # instance_path is described more at https://flask.palletsprojects.com/en/2.1.x/config/
    connexion_app = connexion.FlaskApp(__name__, server_args={"instance_path": os.environ.get("FLASK_INSTANCE_PATH")})
    app = connexion_app.app
    app.config["CONNEXION_APP"] = connexion_app
    app.config["SESSION_TYPE"] = "filesystem"
    _setup_prometheus_metrics(app, connexion_app)

    setup_config(app)
    db.init_app(app)
    migrate.init_app(app, db)

    app.register_blueprint(user_blueprint)
    app.register_blueprint(api_error_blueprint)
    app.register_blueprint(openid_blueprint, url_prefix="/openid")

    # preflight options requests will be allowed if they meet the requirements of the url regex.
    # we will add an Access-Control-Max-Age header to the response to tell the browser it doesn't
    # need to continually keep asking for the same path.
    origins_re = [
        r"^https?:\/\/%s(.*)" % o.replace(".", r"\.") for o in app.config["SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS"]
    ]
    CORS(app, origins=origins_re, max_age=3600, supports_credentials=True)

    connexion_app.add_api("api.yml", base_path=V1_API_PATH_PREFIX)

    mail = Mail(app)
    app.config["MAIL_APP"] = mail

    app.json = MyJSONEncoder(app)

    if should_start_scheduler(app):
        start_scheduler(app)

    configure_sentry(app)

    encryption_lib = app.config.get("SPIFFWORKFLOW_BACKEND_ENCRYPTION_LIB")
    if encryption_lib == "cryptography":
        from cryptography.fernet import Fernet

        app_secret_key = app.config.get("SECRET_KEY")
        app_secret_key_bytes = app_secret_key.encode()
        base64_key = base64.b64encode(app_secret_key_bytes)
        fernet_cipher = Fernet(base64_key)
        app.config["CIPHER"] = fernet_cipher
    # for comparison against possibly-slow encryption libraries
    elif encryption_lib == "no_op_cipher":
        no_op_cipher = NoOpCipher()
        app.config["CIPHER"] = no_op_cipher
    else:
        simple_crypt_cipher = SimpleCrypt()
        app.config["FSC_EXPANSION_COUNT"] = 2048
        simple_crypt_cipher.init_app(app)
        app.config["CIPHER"] = simple_crypt_cipher

    app.before_request(verify_token)
    app.before_request(AuthorizationService.check_for_permission)
    app.after_request(set_new_access_token_in_cookie)

    # The default is true, but we want to preserve the order of keys in the json
    # This is particularly helpful for forms that are generated from json schemas.
    app.json.sort_keys = False

    return app  # type: ignore


def get_version_info_data() -> dict[str, Any]:
    version_info_data_dict = {}
    if os.path.isfile("version_info.json"):
        with open("version_info.json") as f:
            version_info_data_dict = json.load(f)
    return version_info_data_dict


def _setup_prometheus_metrics(app: flask.app.Flask, connexion_app: connexion.apps.flask_app.FlaskApp) -> None:
    metrics = ConnexionPrometheusMetrics(connexion_app)
    app.config["PROMETHEUS_METRICS"] = metrics
    version_info_data = get_version_info_data()
    if len(version_info_data) > 0:
        # prometheus does not allow periods in key names
        version_info_data_normalized = {k.replace(".", "_"): v for k, v in version_info_data.items()}
        metrics.info("version_info", "Application Version Info", **version_info_data_normalized)


def traces_sampler(sampling_context: Any) -> Any:
    # always inherit
    if sampling_context["parent_sampled"] is not None:
        return sampling_context["parent_sampled"]

    if "wsgi_environ" in sampling_context:
        wsgi_environ = sampling_context["wsgi_environ"]
        path_info = wsgi_environ.get("PATH_INFO")
        request_method = wsgi_environ.get("REQUEST_METHOD")

        # tasks_controller.task_submit
        # this is the current pain point as of 31 jan 2023.
        if path_info and (
            (path_info.startswith("/v1.0/tasks/") and request_method == "PUT")
            or (path_info.startswith("/v1.0/task-data/") and request_method == "GET")
        ):
            return 1

    # Default sample rate for all others (replaces traces_sample_rate)
    return 0.01


def configure_sentry(app: flask.app.Flask) -> None:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration

    # get rid of NotFound errors
    def before_send(event: Any, hint: Any) -> Any:
        if "exc_info" in hint:
            _exc_type, exc_value, _tb = hint["exc_info"]
            # NotFound is mostly from web crawlers
            if isinstance(exc_value, NotFound):
                return None
        return event

    sentry_errors_sample_rate = app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE")
    if sentry_errors_sample_rate is None:
        raise Exception("SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE is not set somehow")

    sentry_traces_sample_rate = app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE")
    if sentry_traces_sample_rate is None:
        raise Exception("SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE is not set somehow")

    sentry_env_identifier = app.config["ENV_IDENTIFIER"]
    if app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_ENV_IDENTIFIER"):
        sentry_env_identifier = app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_ENV_IDENTIFIER")

    sentry_configs = {
        "dsn": app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_DSN"),
        "integrations": [
            FlaskIntegration(),
        ],
        "environment": sentry_env_identifier,
        # sample_rate is the errors sample rate. we usually set it to 1 (100%)
        # so we get all errors in sentry.
        "sample_rate": float(sentry_errors_sample_rate),
        # Set traces_sample_rate to capture a certain percentage
        # of transactions for performance monitoring.
        # We recommend adjusting this value to less than 1(00%) in production.
        "traces_sample_rate": float(sentry_traces_sample_rate),
        "traces_sampler": traces_sampler,
        # The profiles_sample_rate setting is relative to the traces_sample_rate setting.
        "before_send": before_send,
    }

    if app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_PROFILING_ENABLED"):
        # profiling doesn't work on windows, because of an issue like https://github.com/nvdv/vprof/issues/62
        # but also we commented out profiling because it was causing segfaults (i guess it is marked experimental)
        profiles_sample_rate = 0 if sys.platform.startswith("win") else 1
        if profiles_sample_rate > 0:
            sentry_configs["_experiments"] = {"profiles_sample_rate": profiles_sample_rate}

    sentry_sdk.init(**sentry_configs)

import json
import os
import sys
from typing import Any

import connexion  # type: ignore
import flask.wrappers
import sentry_sdk
from prometheus_flask_exporter import ConnexionPrometheusMetrics  # type: ignore
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.exceptions import NotFound


def get_version_info_data() -> dict[str, Any]:
    version_info_data_dict = {}
    if os.path.isfile("version_info.json"):
        with open("version_info.json") as f:
            version_info_data_dict = json.load(f)
    return version_info_data_dict


def setup_prometheus_metrics(app: flask.app.Flask, connexion_app: connexion.apps.flask_app.FlaskApp) -> None:
    metrics = ConnexionPrometheusMetrics(connexion_app, group_by="endpoint")
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

    # sample some requests at a higher rate
    # if "wsgi_environ" in sampling_context:
    #     wsgi_environ = sampling_context["wsgi_environ"]
    #     path_info = wsgi_environ.get("PATH_INFO")
    #     request_method = wsgi_environ.get("REQUEST_METHOD")
    #
    #     # tasks_controller.task_submit
    #     # this is the current pain point as of 31 jan 2023.
    #     if path_info and (
    #         (path_info.startswith("/v1.0/tasks/") and request_method == "PUT")
    #         or (path_info.startswith("/v1.0/task-data/") and request_method == "GET")
    #     ):
    #         return 1

    # Default sample rate for all others (replaces traces_sample_rate)
    return 0.01


def configure_sentry(app: flask.app.Flask) -> None:
    # get rid of NotFound errors
    def before_send(event: Any, hint: Any) -> Any:
        if "exc_info" in hint:
            _exc_type, exc_value, _tb = hint["exc_info"]
            # NotFound is mostly from web crawlers
            if isinstance(exc_value, NotFound):
                return None
            if isinstance(exc_value, MethodNotAllowed):
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

    # https://docs.sentry.io/platforms/python/configuration/releases
    version_info_data = get_version_info_data()
    if len(version_info_data) > 0:
        git_commit = version_info_data.get("org.opencontainers.image.revision") or version_info_data.get("git_commit")
        if git_commit is not None:
            sentry_configs["release"] = git_commit

    if app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_PROFILING_ENABLED"):
        # profiling doesn't work on windows, because of an issue like https://github.com/nvdv/vprof/issues/62
        # but also we commented out profiling because it was causing segfaults (i guess it is marked experimental)
        profiles_sample_rate = 0 if sys.platform.startswith("win") else 1
        if profiles_sample_rate > 0:
            sentry_configs["_experiments"] = {"profiles_sample_rate": profiles_sample_rate}

    sentry_sdk.init(**sentry_configs)

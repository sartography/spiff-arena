import json
import os
import sys
from functools import partial
from typing import Any
from typing import cast

import flask.wrappers
import sentry_sdk
from connexion import FlaskApp
from prometheus_flask_exporter import ConnexionPrometheusMetrics  # type: ignore
from sentry_sdk.integrations.flask import FlaskIntegration
from werkzeug.exceptions import NotFound

from spiffworkflow_backend.exceptions.api_error import should_notify_sentry


def get_version_info_data() -> dict[str, Any]:
    version_info_data_dict = {}
    if os.path.isfile("version_info.json"):
        with open("version_info.json") as f:
            version_info_data_dict = json.load(f)
    return version_info_data_dict


def get_public_version_info_data() -> dict[str, Any]:
    version_info_data = get_version_info_data()
    public_version_info_data = {}

    version = version_info_data.get("org.opencontainers.image.version")
    revision = version_info_data.get("org.opencontainers.image.revision")
    created = version_info_data.get("org.opencontainers.image.created")

    if version:
        public_version_info_data["version"] = version
    if revision:
        public_version_info_data["revision"] = revision
    if created:
        public_version_info_data["created"] = created

    return public_version_info_data


def ensure_prometheus_multiproc_dir() -> None:
    prometheus_multiproc_dir = os.environ.get("PROMETHEUS_MULTIPROC_DIR")
    if prometheus_multiproc_dir:
        os.makedirs(prometheus_multiproc_dir, exist_ok=True)


def setup_prometheus_metrics(connexion_app: FlaskApp) -> None:
    ensure_prometheus_multiproc_dir()
    metrics = ConnexionPrometheusMetrics(connexion_app, group_by="endpoint")
    connexion_app.app.config["PROMETHEUS_METRICS"] = metrics
    version_info_data = get_version_info_data()
    if len(version_info_data) > 0:
        # prometheus does not allow periods in key names
        version_info_data_normalized = {k.replace(".", "_"): v for k, v in version_info_data.items()}
        metrics.info("version_info", "Application Version Info", **version_info_data_normalized)


def traces_sampler(sampling_context: Any, default_sample_rate: float = 0.01) -> Any:
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
    #     api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]
    #     if path_info and (
    #         (path_info.startswith(f"{api_path_prefix}/tasks/") and request_method == "PUT")
    #         or (path_info.startswith(f"{api_path_prefix}/task-data/") and request_method == "GET")
    #     ):
    #         return 1

    # Default sample rate for all others (replaces traces_sample_rate)
    return default_sample_rate


def should_capture_exception_in_sentry(exc_value: BaseException) -> bool:
    if isinstance(exc_value, NotFound):
        return False
    status_code = getattr(exc_value, "code", None)
    if status_code is None:
        status_code = getattr(exc_value, "status_code", None)
    if status_code in [404, 405]:
        return False
    if not isinstance(exc_value, Exception):
        return True
    return should_notify_sentry(exc_value)


def scrub_transaction_event(event: dict[str, Any], _hint: Any) -> dict[str, Any]:
    tags = event.get("tags")
    if isinstance(tags, dict):
        tags.pop("url", None)
    elif isinstance(tags, list):
        event["tags"] = [tag for tag in tags if not (isinstance(tag, dict) and tag.get("key") == "url")]
    return event


def _has_usable_exception_info(exc_info: Any) -> bool:
    return (
        isinstance(exc_info, tuple)
        and len(exc_info) == 3
        and isinstance(exc_info[0], type)
        and issubclass(exc_info[0], BaseException)
        and isinstance(exc_info[1], BaseException)
    )


def filter_sentry_error_event(event: dict[str, Any], hint: dict[str, Any]) -> dict[str, Any] | None:
    """Keep exception captures while dropping message-only logs and Flask duplicates."""
    log_record = hint.get("log_record")
    log_record_exc_info = getattr(log_record, "exc_info", None)
    hint_exc_info = hint.get("exc_info")
    exc_info = log_record_exc_info if _has_usable_exception_info(log_record_exc_info) else hint_exc_info

    # Plain messages remain application logs and Sentry breadcrumbs, but do not create Sentry issues.
    # logger.exception() and logger.error(..., exc_info=...) are retained as exception events.
    if not _has_usable_exception_info(exc_info):
        return None
    usable_exc_info = cast(tuple[type[BaseException], BaseException, Any], exc_info)

    exception_values = event.get("exception", {}).get("values", [])

    # we ignore all unhandled flask exceptions for purposes of sentry notification,
    # because these go through handle_exception, where we capture_exception explicitly.
    if any(
        value.get("mechanism", {}).get("type") == "flask" and value.get("mechanism", {}).get("handled") is False
        for value in exception_values
    ):
        return None

    _exc_type, exc_value, _tb = usable_exc_info
    if not should_capture_exception_in_sentry(exc_value):
        return None
    return event


def configure_sentry(app: flask.app.Flask) -> None:
    sentry_dsn = app.config.get("SPIFFWORKFLOW_BACKEND_SENTRY_DSN")

    # Skip Sentry initialization if no DSN is configured (e.g., in tests)
    if not sentry_dsn:
        return

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
        "dsn": sentry_dsn,
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
        "traces_sampler": partial(
            traces_sampler,
            default_sample_rate=float(sentry_traces_sample_rate),
        ),
        # The profiles_sample_rate setting is relative to the traces_sample_rate setting.
        "before_send": filter_sentry_error_event,
        "before_send_transaction": scrub_transaction_event,
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

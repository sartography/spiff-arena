import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest
from flask import Flask
from pytest_mock import MockerFixture
from starlette.exceptions import HTTPException as StarletteHTTPException
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.monitoring_service import configure_sentry
from spiffworkflow_backend.services.monitoring_service import ensure_prometheus_multiproc_dir
from spiffworkflow_backend.services.monitoring_service import filter_sentry_error_event
from spiffworkflow_backend.services.monitoring_service import get_public_version_info_data
from spiffworkflow_backend.services.monitoring_service import scrub_transaction_event
from spiffworkflow_backend.services.monitoring_service import should_capture_exception_in_sentry
from spiffworkflow_backend.services.monitoring_service import traces_sampler
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError


class Generic404HTTPException(HTTPException):
    code = 404


class Generic500HTTPException(HTTPException):
    code = 500


def test_ensure_prometheus_multiproc_dir_creates_configured_directory(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    prometheus_multiproc_dir = tmp_path / "prometheus_multiproc"
    monkeypatch.setenv("PROMETHEUS_MULTIPROC_DIR", str(prometheus_multiproc_dir))

    ensure_prometheus_multiproc_dir()

    assert prometheus_multiproc_dir.is_dir()


def test_get_public_version_info_data_returns_minimal_metadata(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "version_info.json").write_text(
        json.dumps(
            {
                "org.opencontainers.image.version": "main-2026-05-12_17-59-26-6bfb694",
                "org.opencontainers.image.revision": "6bfb694044244009fe3dd78ae987a9dbae218014",
                "org.opencontainers.image.created": "2026-05-12T17:59:27.226Z",
                "org.opencontainers.image.source": "https://github.com/sartography/spiff-arena",
                "version": "ignored-version",
                "revision": "ignored-revision",
                "created": "ignored-created",
                "git_commit": "ignored-git-commit",
            }
        ),
        encoding="utf-8",
    )

    assert get_public_version_info_data() == {
        "version": "main-2026-05-12_17-59-26-6bfb694",
        "revision": "6bfb694044244009fe3dd78ae987a9dbae218014",
        "created": "2026-05-12T17:59:27.226Z",
    }


def test_traces_sampler_uses_configured_default_sample_rate() -> None:
    assert traces_sampler({"parent_sampled": None}, default_sample_rate=0.25) == 0.25


def test_traces_sampler_inherits_parent_sampling_decision() -> None:
    assert traces_sampler({"parent_sampled": True}, default_sample_rate=0.25)
    assert not traces_sampler({"parent_sampled": False}, default_sample_rate=0.25)


def test_scrub_transaction_event_removes_url_tag_from_dict_tags() -> None:
    event = {"type": "transaction", "tags": {"url": "https://example.com/tasks/1/abc", "environment": "prod"}}

    scrubbed_event = scrub_transaction_event(event, {})

    assert scrubbed_event["tags"] == {"environment": "prod"}


def test_scrub_transaction_event_removes_url_tag_from_list_tags() -> None:
    event = {
        "type": "transaction",
        "tags": [
            {"key": "url", "value": "https://example.com/tasks/1/abc"},
            {"key": "environment", "value": "prod"},
        ],
    }

    scrubbed_event = scrub_transaction_event(event, {})

    assert scrubbed_event["tags"] == [{"key": "environment", "value": "prod"}]


def test_filter_sentry_error_event_drops_log_without_exception_info() -> None:
    event = {"logger": "spiffworkflow_backend.services.custom_service_task"}
    hint = {"log_record": Mock(exc_info=None)}

    assert filter_sentry_error_event(event, hint) is None


def test_filter_sentry_error_event_drops_direct_message_without_exception_info() -> None:
    assert filter_sentry_error_event({"message": "boom"}, {}) is None


def test_filter_sentry_error_event_keeps_log_with_exception_info() -> None:
    exception = ValueError("boom")
    exc_info = (ValueError, exception, None)
    event = {
        "logger": "spiffworkflow_backend.services.custom_service_task",
        "exception": {"values": [{"mechanism": {"type": "logging", "handled": True}}]},
    }
    hint = {"log_record": Mock(exc_info=exc_info), "exc_info": exc_info}

    assert filter_sentry_error_event(event, hint) is event


def test_filter_sentry_error_event_drops_implicit_flask_exception() -> None:
    exception = ValueError("boom")
    event = {"exception": {"values": [{"mechanism": {"type": "flask", "handled": False}}]}}
    hint = {"exc_info": (ValueError, exception, None)}

    assert filter_sentry_error_event(event, hint) is None


def test_filter_sentry_error_event_keeps_implicit_celery_exception() -> None:
    exception = ValueError("boom")
    event = {"exception": {"values": [{"mechanism": {"type": "celery", "handled": False}}]}}
    hint = {"exc_info": (ValueError, exception, None)}

    assert filter_sentry_error_event(event, hint) is event


def test_filter_sentry_error_event_keeps_explicit_exception() -> None:
    exception = ValueError("boom")
    event = {"exception": {"values": [{"mechanism": {"type": "generic", "handled": True}}]}}
    hint = {"exc_info": (ValueError, exception, None)}

    assert filter_sentry_error_event(event, hint) is event


def test_configure_sentry_registers_event_filters(mocker: MockerFixture) -> None:
    mock_sentry_init = mocker.patch("spiffworkflow_backend.services.monitoring_service.sentry_sdk.init")
    app = Flask(__name__)
    app.config.update(
        SPIFFWORKFLOW_BACKEND_SENTRY_DSN="https://public@example.com/1",
        SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE=1,
        SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE=0.01,
        SPIFFWORKFLOW_BACKEND_SENTRY_PROFILING_ENABLED=False,
        ENV_IDENTIFIER="unit_testing",
    )

    configure_sentry(app)

    assert mock_sentry_init.call_args.kwargs["before_send"] is filter_sentry_error_event
    assert mock_sentry_init.call_args.kwargs["before_send_transaction"] is scrub_transaction_event


def _sentry_app(**config_overrides: Any) -> Flask:
    app = Flask(__name__)
    app.config.update(
        SPIFFWORKFLOW_BACKEND_SENTRY_DSN="https://public@example.com/1",
        SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE=1,
        SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE=0.01,
        SPIFFWORKFLOW_BACKEND_SENTRY_PROFILING_ENABLED=False,
        ENV_IDENTIFIER="unit_testing",
    )
    app.config.update(config_overrides)
    return app


def test_configure_sentry_defaults_keep_sdk_privacy_behavior(mocker: MockerFixture) -> None:
    mock_sentry_init = mocker.patch("spiffworkflow_backend.services.monitoring_service.sentry_sdk.init")

    configure_sentry(_sentry_app())

    assert mock_sentry_init.call_args.kwargs["include_local_variables"] is True
    assert mock_sentry_init.call_args.kwargs["max_request_body_size"] == "medium"


def test_configure_sentry_passes_privacy_settings(mocker: MockerFixture) -> None:
    mock_sentry_init = mocker.patch("spiffworkflow_backend.services.monitoring_service.sentry_sdk.init")
    app = _sentry_app(
        SPIFFWORKFLOW_BACKEND_SENTRY_INCLUDE_LOCAL_VARIABLES=False,
        SPIFFWORKFLOW_BACKEND_SENTRY_MAX_REQUEST_BODY_SIZE="never",
    )

    configure_sentry(app)

    assert mock_sentry_init.call_args.kwargs["include_local_variables"] is False
    assert mock_sentry_init.call_args.kwargs["max_request_body_size"] == "never"


def test_configure_sentry_rejects_invalid_max_request_body_size(mocker: MockerFixture) -> None:
    mock_sentry_init = mocker.patch("spiffworkflow_backend.services.monitoring_service.sentry_sdk.init")

    with pytest.raises(Exception, match="SPIFFWORKFLOW_BACKEND_SENTRY_MAX_REQUEST_BODY_SIZE"):
        configure_sentry(_sentry_app(SPIFFWORKFLOW_BACKEND_SENTRY_MAX_REQUEST_BODY_SIZE="nope"))

    mock_sentry_init.assert_not_called()


def test_not_found_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(NotFound())


def test_generic_404_http_exception_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(Generic404HTTPException())


def test_starlette_404_http_exception_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(StarletteHTTPException(status_code=404))


def test_generic_500_http_exception_is_captured() -> None:
    assert should_capture_exception_in_sentry(Generic500HTTPException())


def test_starlette_500_http_exception_is_captured() -> None:
    assert should_capture_exception_in_sentry(StarletteHTTPException(status_code=500))


def test_invalid_token_api_error_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(
        ApiError(error_code="invalid_token", message="Cannot validate token.", status_code=401)
    )


def test_invalid_xml_api_error_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(
        ApiError(
            error_code="invalid_xml",
            message="'example.bpmn' is not a valid XML file.",
            status_code=400,
        )
    )


def test_message_not_accepted_api_error_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(
        ApiError(
            error_code="message_not_accepted",
            message="No running process instances correlate with the given message name.",
            status_code=400,
        )
    )


def test_message_rejection_from_lock_contention_is_captured() -> None:
    cause = ProcessInstanceIsAlreadyLockedError("Receiver is locked")
    with pytest.raises(ApiError) as raised:
        MessageService._raise_message_not_accepted("No receiver accepted the message", cause=cause)

    exception = raised.value
    assert exception.status_code == 400
    assert exception.__cause__ is cause
    assert should_capture_exception_in_sentry(exception)
    event: dict[str, Any] = {"exception": {"values": []}}
    assert filter_sentry_error_event(event, {"exc_info": (type(exception), exception, exception.__traceback__)}) is event


def test_missing_process_instance_api_error_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(
        ApiError(
            error_code="process_instance_cannot_be_found",
            message="Process instance cannot be found: 16519",
            status_code=400,
        )
    )


def test_process_instance_has_error_tasks_api_error_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(
        ApiError(
            error_code="process_instance_has_error_tasks",
            message="Cannot resume a process instance while it has errored tasks.",
            status_code=400,
        )
    )


def test_process_instance_validation_api_error_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(
        ApiError(
            error_code="process_instance_validation_error",
            message="Failed to parse the Workflow Specification.",
            status_code=400,
        )
    )


def test_not_authorized_error_is_not_captured() -> None:
    assert not should_capture_exception_in_sentry(NotAuthorizedError())


def test_unexpected_api_error_is_captured() -> None:
    assert should_capture_exception_in_sentry(
        ApiError(error_code="unexpected_workflow_exception", message="Unexpected Workflow Error", status_code=400)
    )

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask
from pytest_mock import MockerFixture

from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing.background_job import HEADER_PREFIX
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job import BackgroundJobPublisher
from spiffworkflow_backend.background_processing.background_job import background_job_context
from spiffworkflow_backend.background_processing.background_job import configured_background_job_publisher
from spiffworkflow_backend.background_processing.background_job_instrumentation import BackgroundJobInstrumentation
from spiffworkflow_backend.services.operation_instrumentation_service import OperationInstrumentation


def test_publisher_attaches_background_job_headers() -> None:
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    def send_task(*args: object, **kwargs: object) -> SimpleNamespace:
        calls.append((args, kwargs))
        return SimpleNamespace(task_id="delivery-1")

    envelope = BackgroundJobEnvelope.create(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": 42, "task_guid": "task-1"},
        countdown=5.25,
        process_instance_id=42,
        task_guid="task-1",
        correlation_id="correlation-1",
        now=100.125,
    )
    published = BackgroundJobPublisher(send_task=send_task).publish(envelope, countdown=5.25)

    assert published.delivery_id == "delivery-1"
    assert calls[0][0] == (CELERY_TASK_PROCESS_INSTANCE_RUN,)
    assert calls[0][1]["kwargs"] == {"process_instance_id": 42, "task_guid": "task-1"}
    assert calls[0][1]["countdown"] == 5.25
    headers = calls[0][1]["headers"]
    assert isinstance(headers, dict)
    assert headers[f"{HEADER_PREFIX}published_at"] == 100.125
    assert headers[f"{HEADER_PREFIX}eligible_at"] == 105.375
    assert headers[f"{HEADER_PREFIX}correlation_id"] == "correlation-1"
    assert f"{HEADER_PREFIX}process_instance_id" not in headers


def test_envelope_message_round_trip() -> None:
    envelope = BackgroundJobEnvelope.create(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": 42, "task_guid": "task-1"},
        countdown=5.25,
        process_instance_id=42,
        task_guid="task-1",
        correlation_id="correlation-1",
        now=100.125,
    )

    assert BackgroundJobEnvelope.from_message(envelope.message()) == envelope


def test_configured_publisher_defaults_to_celery_and_loads_configured_factory(app: Flask, mocker: MockerFixture) -> None:
    external_publisher = object()
    module = SimpleNamespace(create_publisher=mocker.Mock(return_value=external_publisher))
    import_module = mocker.patch(
        "spiffworkflow_backend.background_processing.background_job.importlib.import_module", return_value=module
    )
    with app.app_context():
        assert isinstance(configured_background_job_publisher(), BackgroundJobPublisher)
        original_factory = app.config.get("SPIFFWORKFLOW_BACKEND_BACKGROUND_JOB_PUBLISHER_FACTORY")
        try:
            app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_JOB_PUBLISHER_FACTORY"] = "deployment.publisher:create_publisher"
            publisher = configured_background_job_publisher()
        finally:
            app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_JOB_PUBLISHER_FACTORY"] = original_factory

    assert publisher is external_publisher
    import_module.assert_called_once_with("deployment.publisher")
    module.create_publisher.assert_called_once_with()


def test_decodes_publisher_headers_and_headerless_deliveries() -> None:
    published = BackgroundJobEnvelope.from_delivery(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": 42},
        {
            f"{HEADER_PREFIX}published_at": 10.25,
            f"{HEADER_PREFIX}eligible_at": 12.5,
            f"{HEADER_PREFIX}correlation_id": "correlation-1",
        },
        delivery_job_id="job-1",
        process_instance_id=42,
        now=20.0,
    )
    missing = BackgroundJobEnvelope.from_delivery(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": 43},
        None,
        delivery_job_id="headerless-job",
        process_instance_id=43,
        now=30.5,
    )

    assert published.published_at == 10.25
    assert published.eligible_at == 12.5
    assert published.correlation_id == "correlation-1"
    assert published.process_instance_id == 42
    assert missing.published_at == 30.5
    assert missing.eligible_at == 30.5
    assert missing.correlation_id == "headerless-job"
    assert missing.process_instance_id == 43


def test_malformed_timestamps_fall_back_without_failing_delivery() -> None:
    envelope = BackgroundJobEnvelope.from_delivery(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": 42},
        {
            f"{HEADER_PREFIX}published_at": "not-a-timestamp",
        },
        delivery_job_id="delivered-job",
        process_instance_id=42,
        now=30.5,
    )

    assert envelope.published_at == 30.5
    assert envelope.eligible_at == 30.5
    assert envelope.job_id == "delivered-job"
    assert envelope.process_instance_id == 42


def test_requeue_preserves_correlation_id() -> None:
    original = BackgroundJobEnvelope.create(
        CELERY_TASK_PROCESS_INSTANCE_RUN,
        {"process_instance_id": 42},
        correlation_id="correlation-1",
        now=10.0,
    )
    with background_job_context(original):
        retry = BackgroundJobEnvelope.create(
            CELERY_TASK_PROCESS_INSTANCE_RUN,
            {"process_instance_id": 42},
            now=20.0,
        )

    assert retry.job_id != original.job_id
    assert retry.correlation_id == original.correlation_id


@pytest.mark.parametrize(
    ("published_at", "eligible_at", "started_at", "queue_residence", "queue_wait"),
    [
        (10.0, 10.0, 12.5, 2.5, 2.5),
        (10.0, 20.0, 22.5, 12.5, 2.5),
        (20.0, 20.0, 19.5, 0.0, 0.0),
    ],
)
def test_queue_wait_excludes_eligibility_and_clamps_clock_skew(
    published_at: float,
    eligible_at: float,
    started_at: float,
    queue_residence: float,
    queue_wait: float,
) -> None:
    envelope = BackgroundJobEnvelope(
        job_name=CELERY_TASK_PROCESS_INSTANCE_RUN,
        arguments={"process_instance_id": 42},
        published_at=published_at,
        eligible_at=eligible_at,
        correlation_id="correlation-1",
        job_id="job-1",
    )

    instrumentation = BackgroundJobInstrumentation(envelope, started_at=started_at)

    assert instrumentation.queue_residence_seconds == queue_residence
    assert instrumentation.queue_wait_seconds == queue_wait


def test_observability_failure_does_not_change_operation_result(mocker: MockerFixture) -> None:
    instrumentation = OperationInstrumentation()
    mocker.patch.object(instrumentation, "_record_phase", side_effect=RuntimeError("metrics unavailable"))
    mocker.patch.object(instrumentation, "_record_completion", side_effect=RuntimeError("metrics unavailable"))
    mocker.patch.object(instrumentation, "_log_completion", side_effect=RuntimeError("logging unavailable"))

    with instrumentation.phase("work"):
        result = "customer-result"
    instrumentation.finish_operation("success")
    instrumentation.finish_operation("failed")

    assert result == "customer-result"
    assert instrumentation.finished is True
    assert instrumentation.observability_failures == 3

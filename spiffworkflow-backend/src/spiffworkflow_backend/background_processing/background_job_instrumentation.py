from __future__ import annotations

import time
from typing import Any

from prometheus_client import Counter
from prometheus_client import Histogram

from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_RUN
from spiffworkflow_backend.background_processing import CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE
from spiffworkflow_backend.background_processing.background_job import BackgroundJobEnvelope
from spiffworkflow_backend.background_processing.background_job import _safe_lifecycle_log
from spiffworkflow_backend.services.operation_instrumentation_service import OperationInstrumentation

BACKGROUND_JOB_QUEUE_WAIT_SECONDS = Histogram(
    "spiff_background_job_queue_wait_seconds",
    "Time an eligible Arena background job waited before execution.",
    ["job_name"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 300),
)
BACKGROUND_JOB_OPERATION_TOTAL = Counter(
    "spiff_background_job_operation_total",
    "Arena background job operation outcomes.",
    ["job_name", "outcome"],
)
BACKGROUND_JOB_OPERATION_DURATION_SECONDS = Histogram(
    "spiff_background_job_operation_duration_seconds",
    "Arena background job operation runtime.",
    ["job_name", "outcome"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60, 300, 600),
)
BACKGROUND_JOB_PHASE_DURATION_SECONDS = Histogram(
    "spiff_background_job_phase_duration_seconds",
    "Time spent in bounded Arena background job operation phases.",
    ["job_name", "phase"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

ALLOWED_JOB_NAMES = {
    CELERY_TASK_PROCESS_INSTANCE_RUN,
    CELERY_TASK_PROCESS_INSTANCE_START_FROM_MESSAGE,
}
ALLOWED_OUTCOMES = {"success", "skipped", "locked", "failed"}
ALLOWED_PHASES = {"load", "lock", "engine_run", "persistence", "requeue"}


class BackgroundJobInstrumentation(OperationInstrumentation):
    def __init__(self, envelope: BackgroundJobEnvelope, *, started_at: float | None = None) -> None:
        super().__init__()
        self.envelope = envelope
        self.wall_started_at = time.time() if started_at is None else started_at
        self.queue_residence_seconds = max(0.0, self.wall_started_at - envelope.published_at)
        self.queue_wait_seconds = max(0.0, self.wall_started_at - max(envelope.published_at, envelope.eligible_at))
        try:
            BACKGROUND_JOB_QUEUE_WAIT_SECONDS.labels(job_name=self.job_name_label).observe(self.queue_wait_seconds)
        except Exception:
            self.observability_failures += 1
        _safe_lifecycle_log(
            "Background job started",
            "background_job_started",
            envelope,
            started_at=self.wall_started_at,
            queue_residence_seconds=self.queue_residence_seconds,
            queue_wait_seconds=self.queue_wait_seconds,
        )

    @property
    def job_name_label(self) -> str:
        return self.envelope.job_name if self.envelope.job_name in ALLOWED_JOB_NAMES else "other"

    def _record_phase(self, phase_name: str, duration_seconds: float) -> None:
        phase_label = phase_name if phase_name in ALLOWED_PHASES else "other"
        BACKGROUND_JOB_PHASE_DURATION_SECONDS.labels(job_name=self.job_name_label, phase=phase_label).observe(duration_seconds)

    def _record_completion(self, result: str, duration_seconds: float) -> None:
        outcome_label = result if result in ALLOWED_OUTCOMES else "other"
        BACKGROUND_JOB_OPERATION_TOTAL.labels(job_name=self.job_name_label, outcome=outcome_label).inc()
        BACKGROUND_JOB_OPERATION_DURATION_SECONDS.labels(job_name=self.job_name_label, outcome=outcome_label).observe(
            duration_seconds
        )

    def _log_completion(self, result: str, duration_seconds: float, fields: dict[str, Any]) -> None:
        _safe_lifecycle_log(
            "Background job finished",
            "background_job_finished",
            self.envelope,
            outcome=result,
            finished_at=time.time(),
            runtime_seconds=duration_seconds,
            queue_residence_seconds=self.queue_residence_seconds,
            queue_wait_seconds=self.queue_wait_seconds,
            phase_durations_ms=self.phase_durations_ms,
            **fields,
        )

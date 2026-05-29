from __future__ import annotations

import time
from collections.abc import Generator
from contextlib import contextmanager
from dataclasses import dataclass
from dataclasses import field

from flask import current_app
from prometheus_client import Counter
from prometheus_client import Histogram

MESSAGE_SEND_TOTAL = Counter(
    "spiff_message_send_total",
    "Total message send attempts handled by the backend.",
    ["result", "execution_mode"],
)

MESSAGE_SEND_DURATION_SECONDS = Histogram(
    "spiff_message_send_duration_seconds",
    "Total time spent handling message send attempts.",
    ["result", "execution_mode"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30, 60),
)

MESSAGE_SEND_PHASE_DURATION_SECONDS = Histogram(
    "spiff_message_send_phase_duration_seconds",
    "Time spent in individual message send phases.",
    ["phase", "execution_mode"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10, 30),
)


def _execution_mode_label(execution_mode: str | None) -> str:
    return execution_mode or "default"


@dataclass
class MessageSendInstrumentation:
    modified_message_name: str
    message_name: str
    execution_mode: str | None
    ttl: int
    message_instance_uuid: str | None
    started_at: float = field(default_factory=time.perf_counter)
    phase_durations_ms: dict[str, float] = field(default_factory=dict)
    correlation_result: str | None = None
    finished: bool = False

    @contextmanager
    def phase(self, phase_name: str) -> Generator[None, None, None]:
        phase_started_at = time.perf_counter()
        try:
            yield
        finally:
            duration_seconds = time.perf_counter() - phase_started_at
            self.phase_durations_ms[phase_name] = round(duration_seconds * 1000, 3)
            MESSAGE_SEND_PHASE_DURATION_SECONDS.labels(
                phase=phase_name,
                execution_mode=_execution_mode_label(self.execution_mode),
            ).observe(duration_seconds)

    def set_correlation_result(self, result: str) -> None:
        self.correlation_result = result

    def finish(
        self,
        result: str,
        *,
        message_instance_id: int | None = None,
        receiver_message_instance_id: int | None = None,
        process_instance_id: int | None = None,
        error_code: str | None = None,
    ) -> None:
        if self.finished:
            return
        self.finished = True

        duration_seconds = time.perf_counter() - self.started_at
        execution_mode = _execution_mode_label(self.execution_mode)
        MESSAGE_SEND_TOTAL.labels(result=result, execution_mode=execution_mode).inc()
        MESSAGE_SEND_DURATION_SECONDS.labels(result=result, execution_mode=execution_mode).observe(duration_seconds)

        try:
            logger = current_app.logger
        except RuntimeError:
            return

        logger.info(
            "Message send completed",
            extra={
                "extras": {
                    "event_name": "message_send_completed",
                    "result": result,
                    "duration_ms": round(duration_seconds * 1000, 3),
                    "phase_durations_ms": self.phase_durations_ms,
                    "message_name": self.message_name,
                    "modified_message_name": self.modified_message_name,
                    "execution_mode": execution_mode,
                    "ttl": self.ttl,
                    "has_message_instance_uuid": self.message_instance_uuid is not None,
                    "message_instance_id": message_instance_id,
                    "receiver_message_instance_id": receiver_message_instance_id,
                    "process_instance_id": process_instance_id,
                    "error_code": error_code,
                }
            },
        )

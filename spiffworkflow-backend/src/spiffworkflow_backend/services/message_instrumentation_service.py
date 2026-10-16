from __future__ import annotations

import contextlib
from dataclasses import dataclass

from flask import current_app
from prometheus_client import Counter
from prometheus_client import Histogram
from sqlalchemy.event import listens_for
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import SessionTransaction

from spiffworkflow_backend.services.operation_instrumentation_service import OperationInstrumentation

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

MESSAGE_SEND_EXPIRED_TOTAL = Counter(
    "spiff_message_send_expired_total",
    "Total send messages that expired before any process instance received them.",
    ["reason"],
)


def _execution_mode_label(execution_mode: str | None) -> str:
    return execution_mode or "default"


def log_message_send_expired(
    message_name: str,
    message_instance_id: int,
    message_instance_uuid: str | None,
    reason: str,
) -> None:
    with contextlib.suppress(Exception):
        # Observability must never alter application behavior.
        MESSAGE_SEND_EXPIRED_TOTAL.labels(reason=reason).inc()
    with contextlib.suppress(Exception):
        current_app.logger.info(
            "Message send expired",
            extra={
                "extras": {
                    "event_name": "message_send_expired",
                    "reason": reason,
                    "message_name": message_name,
                    "message_instance_id": message_instance_id,
                    "message_instance_uuid": message_instance_uuid,
                    # Payload-derived diagnostic values stay on the message record, not in logs.
                }
            },
        )


@dataclass
class MessageSendExpiry:
    message_name: str
    message_instance_id: int
    message_instance_uuid: str | None
    reason: str

    def record_after_commit(self, session: Session) -> None:
        """Keep scalar data only: ORM objects cannot be loaded in after_commit."""
        transaction = session.get_nested_transaction() or session.get_transaction()  # type: ignore[attr-defined]
        if transaction is None:
            return
        pending = session.info.setdefault("message_send_expiries", {})
        pending.setdefault(transaction, []).append(self)


@listens_for(Session, "after_commit")  # type: ignore[no-untyped-call,untyped-decorator]
def _record_committed_message_expiries(session: Session) -> None:
    pending = session.info.get("message_send_expiries", {})
    transaction = session.get_nested_transaction() or session.get_transaction()  # type: ignore[attr-defined]
    expiries = pending.pop(transaction, [])
    if transaction is not None and transaction.nested:
        # Releasing a savepoint does not commit its enclosing transaction.
        pending.setdefault(transaction.parent, []).extend(expiries)
        return
    for expiry in expiries:
        log_message_send_expired(
            expiry.message_name,
            expiry.message_instance_id,
            expiry.message_instance_uuid,
            expiry.reason,
        )


@listens_for(Session, "after_transaction_end")  # type: ignore[no-untyped-call,untyped-decorator]
def _discard_message_expiries(session: Session, transaction: SessionTransaction) -> None:
    # Also handles rollback and session.close(), including rolled-back savepoints.
    pending = session.info.get("message_send_expiries", {})
    pending.pop(transaction, None)
    if not pending:
        session.info.pop("message_send_expiries", None)


@dataclass
class MessageSendInstrumentation(OperationInstrumentation):
    modified_message_name: str
    message_name: str
    execution_mode: str | None
    ttl: int
    message_instance_uuid: str | None
    correlation_result: str | None = None
    correlation_lock_error: Exception | None = None

    def __post_init__(self) -> None:
        super().__init__()

    def _record_phase(self, phase_name: str, duration_seconds: float) -> None:
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
        self.finish_operation(
            result,
            message_instance_id=message_instance_id,
            receiver_message_instance_id=receiver_message_instance_id,
            process_instance_id=process_instance_id,
            error_code=error_code,
        )

    def _record_completion(self, result: str, duration_seconds: float) -> None:
        execution_mode = _execution_mode_label(self.execution_mode)
        MESSAGE_SEND_TOTAL.labels(result=result, execution_mode=execution_mode).inc()
        MESSAGE_SEND_DURATION_SECONDS.labels(result=result, execution_mode=execution_mode).observe(duration_seconds)

    def _log_completion(self, result: str, duration_seconds: float, fields: dict[str, object]) -> None:
        try:
            logger = current_app.logger
        except RuntimeError:
            return
        execution_mode = _execution_mode_label(self.execution_mode)

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
                    "message_instance_uuid": self.message_instance_uuid,
                    **fields,
                }
            },
        )

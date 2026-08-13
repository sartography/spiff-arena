from __future__ import annotations

import time
import uuid
from collections.abc import Generator
from collections.abc import Mapping
from contextlib import contextmanager
from contextlib import suppress
from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import celery
from flask import current_app

ENVELOPE_VERSION = 1
LIFECYCLE_EVENT_SCHEMA_VERSION = 1
HEADER_PREFIX = "spiff_background_job_"

JobArgument = str | int | float | bool | None


@dataclass(frozen=True)
class BackgroundJobEnvelope:
    job_name: str
    arguments: dict[str, JobArgument]
    published_at: float
    eligible_at: float
    correlation_id: str
    job_id: str
    original_job_id: str
    attempt: int = 1
    process_instance_id: int | None = None
    task_guid: str | None = None
    trace_id: str | None = None
    version: int = ENVELOPE_VERSION

    @classmethod
    def create(
        cls,
        job_name: str,
        arguments: Mapping[str, JobArgument],
        *,
        countdown: float | None = None,
        process_instance_id: int | None = None,
        task_guid: str | None = None,
        correlation_id: str | None = None,
        trace_id: str | None = None,
        now: float | None = None,
    ) -> BackgroundJobEnvelope:
        published_at = time.time() if now is None else now
        eligible_at = published_at + max(0.0, countdown or 0.0)
        parent = _CURRENT_BACKGROUND_JOB.get()
        job_id = str(uuid.uuid4())
        same_logical_job = parent is not None and parent.job_name == job_name
        original_job_id = parent.original_job_id if same_logical_job and parent is not None else job_id
        attempt = parent.attempt + 1 if same_logical_job and parent is not None else 1
        return cls(
            job_name=job_name,
            arguments=dict(arguments),
            published_at=published_at,
            eligible_at=eligible_at,
            correlation_id=correlation_id or (parent.correlation_id if parent else str(uuid.uuid4())),
            job_id=job_id,
            original_job_id=original_job_id,
            attempt=attempt,
            process_instance_id=process_instance_id,
            task_guid=task_guid,
            trace_id=trace_id or (parent.trace_id if parent else None),
        )

    @classmethod
    def from_delivery(
        cls,
        job_name: str,
        arguments: Mapping[str, JobArgument],
        headers: dict[str, Any] | None,
        *,
        delivery_job_id: str | None = None,
        now: float | None = None,
    ) -> BackgroundJobEnvelope:
        """Decode v1 headers and the previous header-less/v0 delivery format."""
        headers = headers or {}
        received_at = time.time() if now is None else now
        version = _safe_int(headers.get(f"{HEADER_PREFIX}envelope_version"), 0)
        # Unknown or malformed telemetry must not change execution of the delivered job.
        if version not in (0, ENVELOPE_VERSION):
            version = 0

        def header(name: str, legacy_name: str | None = None) -> Any:
            value = headers.get(f"{HEADER_PREFIX}{name}")
            if value is None and version == 0 and legacy_name is not None:
                value = headers.get(legacy_name)
            return value

        job_id = str(header("job_id", "job_id") or delivery_job_id or uuid.uuid4())
        published_at = _safe_float(header("published_at", "published_at"), received_at)
        eligible_at = _safe_float(header("eligible_at", "eligible_at"), published_at)
        process_instance_id = _optional_int(header("process_instance_id"))
        task_guid = _optional_str(header("task_guid"))
        return cls(
            version=version,
            job_name=job_name,
            arguments=dict(arguments),
            published_at=published_at,
            eligible_at=eligible_at,
            correlation_id=str(header("correlation_id", "correlation_id") or job_id),
            job_id=job_id,
            original_job_id=str(header("original_job_id", "original_job_id") or job_id),
            attempt=max(1, _safe_int(header("attempt", "attempt"), 1)),
            process_instance_id=(
                process_instance_id if process_instance_id is not None else _optional_int(arguments.get("process_instance_id"))
            ),
            task_guid=task_guid if task_guid is not None else _optional_str(arguments.get("task_guid")),
            trace_id=_optional_str(header("trace_id", "trace_id")),
        )

    def headers(self) -> dict[str, JobArgument]:
        return {
            f"{HEADER_PREFIX}envelope_version": self.version,
            f"{HEADER_PREFIX}published_at": self.published_at,
            f"{HEADER_PREFIX}eligible_at": self.eligible_at,
            f"{HEADER_PREFIX}correlation_id": self.correlation_id,
            f"{HEADER_PREFIX}job_id": self.job_id,
            f"{HEADER_PREFIX}original_job_id": self.original_job_id,
            f"{HEADER_PREFIX}attempt": self.attempt,
            f"{HEADER_PREFIX}process_instance_id": self.process_instance_id,
            f"{HEADER_PREFIX}task_guid": self.task_guid,
            f"{HEADER_PREFIX}trace_id": self.trace_id,
        }

    def structured_fields(self) -> dict[str, JobArgument]:
        return {
            "schema_version": LIFECYCLE_EVENT_SCHEMA_VERSION,
            "job_name": self.job_name,
            "correlation_id": self.correlation_id,
            "job_id": self.job_id,
            "original_job_id": self.original_job_id,
            "attempt": self.attempt,
            "process_instance_id": self.process_instance_id,
            "task_guid": self.task_guid,
            "trace_id": self.trace_id,
        }


@dataclass(frozen=True)
class PublishedBackgroundJob:
    envelope: BackgroundJobEnvelope
    delivery_id: str


@dataclass
class BackgroundJobPublisher:
    send_task: Any = field(default_factory=lambda: celery.current_app.send_task)

    def publish(self, envelope: BackgroundJobEnvelope, *, countdown: float | None = None) -> PublishedBackgroundJob:
        async_result = self.send_task(
            envelope.job_name,
            kwargs=envelope.arguments,
            headers=envelope.headers(),
            **({"countdown": countdown} if countdown is not None else {}),
        )
        delivery_id = str(async_result.task_id)
        _safe_lifecycle_log(
            "Background job enqueued",
            "background_job_enqueued",
            envelope,
            delivery_id=delivery_id,
            published_at=envelope.published_at,
            eligible_at=envelope.eligible_at,
        )
        return PublishedBackgroundJob(envelope=envelope, delivery_id=delivery_id)


_CURRENT_BACKGROUND_JOB: ContextVar[BackgroundJobEnvelope | None] = ContextVar("current_background_job", default=None)


@contextmanager
def background_job_context(envelope: BackgroundJobEnvelope) -> Generator[None, None, None]:
    token = _CURRENT_BACKGROUND_JOB.set(envelope)
    try:
        yield
    finally:
        _CURRENT_BACKGROUND_JOB.reset(token)


def _safe_lifecycle_log(message: str, event_name: str, envelope: BackgroundJobEnvelope, **fields: Any) -> None:
    try:
        current_app.logger.info(
            message,
            extra={"extras": {"event_name": event_name, **envelope.structured_fields(), **fields}},
        )
    except Exception:
        return


def before_task_publish_handler(sender: Any = None, headers: dict | None = None, body: Any = None, **kwargs: Any) -> None:
    """Compatibility fallback for tasks published without BackgroundJobPublisher.

    Legacy callers using celery send_task directly get envelope metadata so
    workers can still compute publication/eligibility lineage. Publisher-set
    headers are never overwritten.
    """
    if headers is None:
        return
    with suppress(Exception):
        # Signal handlers must never break publication.
        now = time.time()
        headers.setdefault(f"{HEADER_PREFIX}envelope_version", ENVELOPE_VERSION)
        headers.setdefault(f"{HEADER_PREFIX}published_at", now)
        headers.setdefault(f"{HEADER_PREFIX}eligible_at", headers[f"{HEADER_PREFIX}published_at"])
        headers.setdefault(f"{HEADER_PREFIX}job_id", str(uuid.uuid4()))
        headers.setdefault(f"{HEADER_PREFIX}attempt", 1)


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_str(value: Any) -> str | None:
    return None if value is None else str(value)


def _safe_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

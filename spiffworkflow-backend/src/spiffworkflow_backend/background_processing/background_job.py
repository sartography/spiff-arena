from __future__ import annotations

import time
import uuid
from collections.abc import Generator
from collections.abc import Mapping
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass
from dataclasses import field
from typing import Any

import celery
from flask import current_app

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
    process_instance_id: int | None = None
    task_guid: str | None = None

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
        now: float | None = None,
    ) -> BackgroundJobEnvelope:
        published_at = time.time() if now is None else now
        eligible_at = published_at + max(0.0, countdown or 0.0)
        parent = _CURRENT_BACKGROUND_JOB.get()
        job_id = str(uuid.uuid4())
        return cls(
            job_name=job_name,
            arguments=dict(arguments),
            published_at=published_at,
            eligible_at=eligible_at,
            correlation_id=correlation_id or (parent.correlation_id if parent else str(uuid.uuid4())),
            job_id=job_id,
            process_instance_id=process_instance_id,
            task_guid=task_guid,
        )

    @classmethod
    def from_delivery(
        cls,
        job_name: str,
        arguments: Mapping[str, JobArgument],
        headers: dict[str, Any] | None,
        *,
        delivery_job_id: str | None = None,
        process_instance_id: int | None = None,
        task_guid: str | None = None,
        now: float | None = None,
    ) -> BackgroundJobEnvelope:
        """Build an envelope from publisher headers or a headerless delivery."""
        headers = headers or {}
        received_at = time.time() if now is None else now
        job_id = str(headers.get(f"{HEADER_PREFIX}job_id") or delivery_job_id or uuid.uuid4())
        published_at = _safe_float(headers.get(f"{HEADER_PREFIX}published_at"), received_at)
        eligible_at = _safe_float(headers.get(f"{HEADER_PREFIX}eligible_at"), published_at)
        return cls(
            job_name=job_name,
            arguments=dict(arguments),
            published_at=published_at,
            eligible_at=eligible_at,
            correlation_id=str(headers.get(f"{HEADER_PREFIX}correlation_id") or job_id),
            job_id=job_id,
            process_instance_id=process_instance_id,
            task_guid=task_guid,
        )

    def headers(self) -> dict[str, JobArgument]:
        return {
            f"{HEADER_PREFIX}published_at": self.published_at,
            f"{HEADER_PREFIX}eligible_at": self.eligible_at,
            f"{HEADER_PREFIX}correlation_id": self.correlation_id,
            f"{HEADER_PREFIX}job_id": self.job_id,
        }

    def structured_fields(self) -> dict[str, JobArgument]:
        return {
            "job_name": self.job_name,
            "correlation_id": self.correlation_id,
            "job_id": self.job_id,
            "process_instance_id": self.process_instance_id,
            "task_guid": self.task_guid,
        }


@dataclass(frozen=True)
class PublishedBackgroundJob:
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
        return PublishedBackgroundJob(delivery_id=delivery_id)


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


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

import threading
from typing import Any

from flask import current_app
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel


class ExpectedLockNotFoundError(Exception):
    pass


class ProcessInstanceLockService:
    """TODO: comment."""

    @classmethod
    def set_thread_local_locking_context(cls, domain: str) -> None:
        current_app.config["THREAD_LOCAL_DATA"].lock_service_context = {
            "domain": domain,
            "uuid": current_app.config["PROCESS_UUID"],
            "thread_id": threading.get_ident(),
            "locks": {},
        }

    @classmethod
    def get_thread_local_locking_context(cls) -> dict[str, Any]:
        tld = current_app.config["THREAD_LOCAL_DATA"]
        if not hasattr(tld, "lock_service_context"):
            cls.set_thread_local_locking_context("web")
        return tld.lock_service_context  # type: ignore

    @classmethod
    def locked_by(cls) -> str:
        ctx = cls.get_thread_local_locking_context()
        return f"{ctx['domain']}:{ctx['uuid']}:{ctx['thread_id']}"

    @classmethod
    def lock(cls, process_instance_id: int, queue_entry: ProcessInstanceQueueModel) -> None:
        ctx = cls.get_thread_local_locking_context()
        ctx["locks"][process_instance_id] = queue_entry

    @classmethod
    def lock_many(cls, queue_entries: list[ProcessInstanceQueueModel]) -> list[int]:
        ctx = cls.get_thread_local_locking_context()
        new_locks = {entry.process_instance_id: entry for entry in queue_entries}
        new_lock_ids = list(new_locks.keys())
        ctx["locks"].update(new_locks)
        return new_lock_ids

    @classmethod
    def unlock(cls, process_instance_id: int) -> ProcessInstanceQueueModel:
        queue_model = cls.try_unlock(process_instance_id)
        if queue_model is None:
            raise ExpectedLockNotFoundError(f"Could not find a lock for process instance: {process_instance_id}")
        return queue_model

    @classmethod
    def try_unlock(cls, process_instance_id: int) -> ProcessInstanceQueueModel | None:
        ctx = cls.get_thread_local_locking_context()
        return ctx["locks"].pop(process_instance_id, None)  # type: ignore

    @classmethod
    def has_lock(cls, process_instance_id: int) -> bool:
        ctx = cls.get_thread_local_locking_context()
        return process_instance_id in ctx["locks"]

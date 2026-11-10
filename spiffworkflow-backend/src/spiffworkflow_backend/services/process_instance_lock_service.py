import threading
import time
from typing import Any

from billiard import current_process  # type: ignore
from flask import current_app
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel


class ExpectedLockNotFoundError(Exception):
    pass


class ProcessInstanceLockService:
    # when we lock process instances, we need to make sure we do not use the same locking identifier
    # as anything else, or else we will use their lock and be unintentionally stomping on the same
    # process instance as them. this happened with celery workers. we generated a guid on startup
    # in backend, but this same guid was used by all concurrent celery workers. to mitigate this,
    # and make sure they weren't trying to use each others locks, we found out about billiard.current_process(),
    # which can give us a unique index for each worker even if they are running in the same python process.
    # if we are not in celery, get_current_process_index will return None, and that is also fine, since
    # if we are not in celery, there is no concern about multiple things happening at once in a process (other than.
    # theading, which is accounted for by the thread_id).
    @classmethod
    def get_current_process_index(cls) -> Any:
        process = current_process()
        index = getattr(process, "index", None)
        return index

    @classmethod
    def set_thread_local_locking_context(cls, domain: str) -> None:
        tld = current_app.config["THREAD_LOCAL_DATA"]
        if not hasattr(tld, "lock_service_context"):
            tld.lock_service_context = {}
        tld.lock_service_context[cls.get_current_process_index()] = {
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
        return tld.lock_service_context[cls.get_current_process_index()]  # type: ignore

    @classmethod
    def locked_by(cls) -> str:
        ctx = cls.get_thread_local_locking_context()
        return f"{ctx['domain']}:{ctx['uuid']}:{ctx['thread_id']}:{cls.get_current_process_index()}"

    @classmethod
    def lock(cls, process_instance_id: int, queue_entry: ProcessInstanceQueueModel) -> None:
        ctx = cls.get_thread_local_locking_context()
        ctx["locks"][process_instance_id] = queue_entry.id

    @classmethod
    def unlock(cls, process_instance_id: int) -> int:
        queue_model_id = cls.try_unlock(process_instance_id)
        if queue_model_id is None:
            raise ExpectedLockNotFoundError(f"Could not find a lock for process instance: {process_instance_id}")
        return queue_model_id

    @classmethod
    def try_unlock(cls, process_instance_id: int) -> int | None:
        ctx = cls.get_thread_local_locking_context()
        return ctx["locks"].pop(process_instance_id, None)  # type: ignore

    @classmethod
    def has_lock(cls, process_instance_id: int) -> bool:
        ctx = cls.get_thread_local_locking_context()
        return process_instance_id in ctx["locks"]

    @classmethod
    def stale_locks(cls) -> list[Any]:
        """Locks that have been held for longer than the max lock duration, as plain rows."""
        max_duration = current_app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"]
        five_min_ago = round(time.time()) - max_duration

        # TODO: remove check for NULL locked_at_in_seconds and fallback to updated_at_in_seconds
        #   once we can confirm that old entries have been taken care of on current envs.
        # New code should not allow rows where locked_by has a value but locked_at_in_seconds is null.
        return (
            db.session.query(
                ProcessInstanceQueueModel.id,
                ProcessInstanceQueueModel.process_instance_id,
                ProcessInstanceQueueModel.locked_by,
                ProcessInstanceQueueModel.locked_at_in_seconds,
                ProcessInstanceQueueModel.updated_at_in_seconds,
            )
            .filter(
                ProcessInstanceQueueModel.locked_by != None,  # noqa: E711
                or_(
                    ProcessInstanceQueueModel.locked_at_in_seconds <= five_min_ago,
                    and_(
                        ProcessInstanceQueueModel.updated_at_in_seconds <= five_min_ago,
                        ProcessInstanceQueueModel.locked_at_in_seconds == None,  # noqa: E711
                    ),
                ),
            )
            .all()
        )

    @classmethod
    def remove_stale_lock(cls, stale_lock: Any) -> bool:
        """Remove a lock found by stale_locks, unless it has been released since. Does not commit."""
        current_time = round(time.time())
        locked_duration = current_time - (stale_lock.locked_at_in_seconds or stale_lock.updated_at_in_seconds)
        current_app.logger.info(
            f"Removing stale lock for process instance: {stale_lock.process_instance_id} with locked_by:"
            f" '{stale_lock.locked_by}' because it has been locked for seconds: {locked_duration}"
        )
        lock_removed = ProcessInstanceQueueModel.query.filter_by(
            id=stale_lock.id, locked_by=stale_lock.locked_by, locked_at_in_seconds=stale_lock.locked_at_in_seconds
        ).update(
            {"locked_by": None, "locked_at_in_seconds": None, "updated_at_in_seconds": current_time},
            synchronize_session=False,
        )
        return bool(lock_removed)

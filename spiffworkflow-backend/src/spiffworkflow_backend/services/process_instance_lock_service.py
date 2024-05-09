from billiard import current_process  # type: ignore
import threading
import time
from typing import Any

from flask import current_app
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel


class ExpectedLockNotFoundError(Exception):
    pass


class ProcessInstanceLockService:
    """TODO: comment."""

    @classmethod
    def get_current_process_index(cls) -> Any:
        process = current_process()
        index = None
        if hasattr(process, "index"):
            index = current_process().index
        print(f"➡️ ➡️ ➡️  index: {index}")
        return index

    @classmethod
    def set_thread_local_locking_context(cls, domain: str, additional_processing_identifier: str | None = None) -> None:
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
    def get_thread_local_locking_context(cls, additional_processing_identifier: str | None = None) -> dict[str, Any]:
        tld = current_app.config["THREAD_LOCAL_DATA"]
        if not hasattr(tld, "lock_service_context"):
            cls.set_thread_local_locking_context("web", additional_processing_identifier=additional_processing_identifier)
        return tld.lock_service_context[cls.get_current_process_index()]  # type: ignore

    @classmethod
    def locked_by(cls, additional_processing_identifier: str | None = None) -> str:
        ctx = cls.get_thread_local_locking_context(additional_processing_identifier=additional_processing_identifier)
        return f"{ctx['domain']}:{ctx['uuid']}:{ctx['thread_id']}:{cls.get_current_process_index()}"

    @classmethod
    def lock(
        cls, process_instance_id: int, queue_entry: ProcessInstanceQueueModel, additional_processing_identifier: str | None = None
    ) -> None:
        ctx = cls.get_thread_local_locking_context(additional_processing_identifier=additional_processing_identifier)
        ctx["locks"][process_instance_id] = queue_entry.id

    @classmethod
    def unlock(cls, process_instance_id: int, additional_processing_identifier: str | None = None) -> int:
        queue_model_id = cls.try_unlock(process_instance_id, additional_processing_identifier=additional_processing_identifier)
        if queue_model_id is None:
            raise ExpectedLockNotFoundError(f"Could not find a lock for process instance: {process_instance_id}")
        return queue_model_id

    @classmethod
    def try_unlock(cls, process_instance_id: int, additional_processing_identifier: str | None = None) -> int | None:
        ctx = cls.get_thread_local_locking_context(additional_processing_identifier=additional_processing_identifier)
        return ctx["locks"].pop(process_instance_id, None)  # type: ignore

    @classmethod
    def has_lock(cls, process_instance_id: int, additional_processing_identifier: str | None = None) -> bool:
        ctx = cls.get_thread_local_locking_context(additional_processing_identifier=additional_processing_identifier)
        current_app.logger.info(f"THREAD LOCK: {ctx}")
        return process_instance_id in ctx["locks"]

    @classmethod
    def remove_stale_locks(cls) -> None:
        max_duration = current_app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"]
        current_time = round(time.time())
        five_min_ago = current_time - max_duration

        # TODO: remove check for NULL locked_at_in_seconds and fallback to updated_at_in_seconds
        #   once we can confirm that old entries have been taken care of on current envs.
        # New code should not allow rows where locked_by has a value but locked_at_in_seconds is null.
        entries_with_stale_locks = ProcessInstanceQueueModel.query.filter(
            ProcessInstanceQueueModel.locked_by != None,  # noqa: E711
            or_(
                ProcessInstanceQueueModel.locked_at_in_seconds <= five_min_ago,
                and_(
                    ProcessInstanceQueueModel.updated_at_in_seconds <= five_min_ago,
                    ProcessInstanceQueueModel.locked_at_in_seconds == None,  # noqa: E711
                ),
            ),
        ).all()

        for entry in entries_with_stale_locks:
            locked_duration = current_time - (entry.locked_at_in_seconds or entry.updated_at_in_seconds)
            current_app.logger.info(
                f"Removing stale lock for process instance: {entry.process_instance_id} with locked_by:"
                f" '{entry.locked_by}' because it has been locked for seconds: {locked_duration}"
            )
            entry.locked_by = None
            entry.locked_at_in_seconds = None
            db.session.add(entry)
            db.session.commit()

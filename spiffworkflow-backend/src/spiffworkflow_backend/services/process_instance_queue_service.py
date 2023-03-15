import time
from typing import List
from typing import Optional

from flask import current_app

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_queue import (
    ProcessInstanceQueueModel,
)
from spiffworkflow_backend.services.process_instance_lock_service import (
    ProcessInstanceLockService,
)


class ProcessInstanceIsNotEnqueuedError(Exception):
    pass


class ProcessInstanceIsAlreadyLockedError(Exception):
    pass


class ProcessInstanceQueueService:
    """TODO: comment."""

    @staticmethod
    def enqueue(process_instance: ProcessInstanceModel) -> None:
        queue_item = ProcessInstanceLockService.try_unlock(process_instance.id)

        if queue_item is None:
            queue_item = ProcessInstanceQueueModel(
                process_instance_id=process_instance.id
            )

        # TODO: configurable params (priority/run_at)
        queue_item.run_at_in_seconds = round(time.time())
        queue_item.priority = 2
        queue_item.status = process_instance.status
        queue_item.locked_by = None
        queue_item.locked_at_in_seconds = None

        db.session.add(queue_item)
        db.session.commit()

    @staticmethod
    def dequeue(process_instance: ProcessInstanceModel) -> None:
        if ProcessInstanceLockService.has_lock(process_instance.id):
            return

        locked_by = ProcessInstanceLockService.locked_by()

        db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.process_instance_id == process_instance.id,
            ProcessInstanceQueueModel.locked_by.is_(None),  # type: ignore
        ).update(
            {
                "locked_by": locked_by,
            }
        )

        db.session.commit()

        queue_entry = (
            db.session.query(ProcessInstanceQueueModel)
            .filter(
                ProcessInstanceQueueModel.process_instance_id == process_instance.id,
            )
            .first()
        )

        if queue_entry is None:
            raise ProcessInstanceIsNotEnqueuedError(
                f"{locked_by} cannot lock process instance {process_instance.id}. It"
                " has not been enqueued."
            )

        if queue_entry.locked_by != locked_by:
            raise ProcessInstanceIsAlreadyLockedError(
                f"{locked_by} cannot lock process instance {process_instance.id}. "
                f"It has already been locked by {queue_entry.locked_by}."
            )

        ProcessInstanceLockService.lock(process_instance.id, queue_entry)

    @classmethod
    def entries_with_status(
        cls,
        status_value: str = ProcessInstanceStatus.waiting.value,
        locked_by: Optional[str] = None,
    ) -> List[ProcessInstanceQueueModel]:
        return (
            db.session.query(ProcessInstanceQueueModel)
            .filter(
                ProcessInstanceQueueModel.status == status_value,
                ProcessInstanceQueueModel.locked_by == locked_by,
            )
            .all()
        )

    @classmethod
    def peek_many(
        cls,
        status_value: str = ProcessInstanceStatus.waiting.value,
    ) -> List[int]:
        queue_entries = cls.entries_with_status(status_value, None)
        ids_with_status = [entry.process_instance_id for entry in queue_entries]
        return ids_with_status

    @classmethod
    def dequeue_many(
        cls,
        status_value: str = ProcessInstanceStatus.waiting.value,
    ) -> List[int]:
        locked_by = ProcessInstanceLockService.locked_by()

        # TODO: configurable params (priority/run_at/limit)
        db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.status == status_value,
            ProcessInstanceQueueModel.locked_by.is_(None),  # type: ignore
        ).update(
            {
                "locked_by": locked_by,
            }
        )

        db.session.commit()

        queue_entries = cls.entries_with_status(status_value, locked_by)

        locked_ids = ProcessInstanceLockService.lock_many(queue_entries)

        if len(locked_ids) > 0:
            current_app.logger.info(f"{locked_by} dequeued_many: {locked_ids}")

        return locked_ids

import logging
import threading
import time
from typing import Callable
from typing import List

from flask import current_app

from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance_correlation import (
    MessageInstanceCorrelationRuleModel,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService


class ProcessInstanceIsAlreadyLockedError(Exception):
    pass


class ProcessInstanceQueueService:
    """TODO: comment"""

    @staticmethod
    def enqueue(process_instance: ProcessInstanceModel) -> None:
        queue_item = ProcessInstanceLockService.try_unlock(process_instance.id)
        
        if queue_item is None:
            queue_item = ProcessInstanceQueueModel(process_instance_id=process_instance.id)

        # TODO: configurable params (priority/run_at)
        queue_item.run_at_in_seconds=round(time.time())
        queue_item.priority=2
        queue_item.status=process_instance.status
        queue_item.locked_by=None
        queue_item.locked_at_in_seconds=None

        db.session.add(queue_item)
        db.session.commit()


    @staticmethod
    def dequeue(process_instance: ProcessInstanceModel) -> None:
        if ProcessInstanceLockService.has_lock(process_instance.id):
            return

        locked_by = ProcessInstanceLockService.locked_by()

        db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.process_instance_id==process_instance.id,
            ProcessInstanceQueueModel.locked_by==None,
        ).update({
            "locked_by": locked_by,
        })

        db.session.commit()

        queue_entry = db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.process_instance_id==process_instance.id,
            ProcessInstanceQueueModel.locked_by==locked_by,
        ).first()

        if queue_entry is None:
            raise ProcessInstanceIsAlreadyLockedError(
                f"Cannot lock process instance {process_instance.id}. "
                "It has already been locked or has not been enqueued."
            )

        ProcessInstanceLockService.lock(process_instance.id, queue_entry)
        

    @staticmethod
    def dequeue_many(status_value: str = ProcessInstanceStatus.waiting.value) -> List[int]:

        locked_by = ProcessInstanceLockService.locked_by()

        # TODO: configurable params (priority/run_at/limit)
        db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.status==status_value,
            ProcessInstanceQueueModel.locked_by==None,
        ).update({
            "locked_by": locked_by,
        })

        db.session.commit()

        queue_entries = db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.status==status_value,
            ProcessInstanceQueueModel.locked_by==locked_by,
        ).all()

        locked_ids = ProcessInstanceLockService.lock_many(queue_entries)

        if len(locked_ids) > 0:
            current_app.logger.info(f"{locked_by} dequeued_many: {locked_ids}")

        return locked_ids

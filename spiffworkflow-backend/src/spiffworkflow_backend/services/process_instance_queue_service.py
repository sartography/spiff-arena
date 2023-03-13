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
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService


#
# use cases:
#
# process_instance_create:
#   - no previous entry in the queue
#   - calls: enqueue (insert)
#
# process_instance_run:
#   - should have an existing entry in the queue from previous `create`
#   - calls `dequeue`
#
# task_submit:
#   - should have an existing entry in the queue from previous `run`
#   - calls: dequeue
#
# do_engine_steps:
#   - when done executing, add back to the queue
#   - calls: enqueue (update)
#
# background processors:
#   - are not tied to a specific process instance id, just need to run things
#   - calls: dequeue_many (flavors?)
#

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
        locked_by = ProcessInstanceLockService.locked_by()

        db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.process_instance_id==process_instance.id,
            ProcessInstanceQueueModel.locked_by==None,
        ).update({
            "locked_by": ProcessInstanceLockService.locked_by(),
        })

        db.session.commit()

        queue_entry = db.session.query(ProcessInstanceQueueModel).filter(
            ProcessInstanceQueueModel.process_instance_id==process_instance.id,
        ).first()

        if queue_entry is None:
            raise ApiError(
                    "process_not_in_queue",
                    "The process instance has not been added to the queue."
                )

        if queue_entry.locked_by != locked_by:
            raise ApiError(
                    "process already locked",
                    "The process instance has already been locked by another thread."
                )

        ProcessInstanceLockService.lock(process_instance.id, queue_entry)
        

    @staticmethod
    def dequeue_many():
        pass

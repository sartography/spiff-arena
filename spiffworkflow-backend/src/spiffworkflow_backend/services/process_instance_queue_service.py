import logging
import threading
import time
from typing import Callable
from typing import List

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
        # TODO: check if lock is held by thread, if so update else insert
        # TODO: configurable params (priority/run_at)
        queue_item = ProcessInstanceQueueModel(
            process_instance_id=process_instance.id,
            run_at_in_seconds=round(time.time()),
            priority=2,
            status=process_instance.status,
            locked_by=None,
            locked_at_in_seconds=None,
        )
        db.session.add(queue_item)
        db.session.commit()


    @staticmethod
    def dequeue(process_instance: ProcessInstanceModel) -> None:
        pass

    @staticmethod
    def dequeue_many():
        pass

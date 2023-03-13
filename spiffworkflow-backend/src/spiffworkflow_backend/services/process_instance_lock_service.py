import logging
import threading
import time
from typing import Callable
from typing import List
from typing import Optional

import flask.app
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


class ProcessInstanceLockService:
    """TODO: comment."""

    @staticmethod
    def set_thread_local_locking_context(app: flask.app.Flask, domain: str) -> None:
        app.config["LOCK_SERVICE_CONTEXT"] = [
            domain,
            str(app.config["PROCESS_UUID"]),
            str(threading.get_ident()),
        ]

    @classmethod
    def _locked_ids(cls) -> set[int]:
        # TODO: want to find the highest entry point after THREAD_LOCAL_DATA has been 
        # set so this doesn't have to be lazy loaded. __init__ was too early to set 
        # in `set_thread_local_locking_context`
        tld = current_app.config["THREAD_LOCAL_DATA"]
        if not hasattr(tld, "locked_process_instance_ids"):
            tld.locked_process_instance_ids = {}
        return tld.locked_process_instance_ids

    @staticmethod
    def locked_by() -> str:
        # TODO: probably just do this in `set_thread_local_locking_context`
        return ":".join(current_app.config["LOCK_SERVICE_CONTEXT"])

    @classmethod
    def lock(cls, process_instance_id: int, queue_entry: ProcessInstanceQueueModel) -> None:
        cls._locked_ids()[process_instance_id] = queue_entry

    @classmethod
    def unlock(cls, process_instance_id: int) -> ProcessInstanceQueueModel:
        cls._locked_ids().pop(process_instance_id)

    @classmethod
    def try_unlock(cls, process_instance_id: int) -> Optional[ProcessInstanceQueueModel]:
        return cls._locked_ids().pop(process_instance_id, None)

    @classmethod
    def has_lock(cls, process_instance_id: int) -> bool:
        return process_instance_id in cls._locked_ids()


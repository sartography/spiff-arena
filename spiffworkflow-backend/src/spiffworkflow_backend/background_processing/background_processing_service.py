import time

import flask
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_future_task_if_appropriate,
)
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


class BackgroundProcessingService:
    """Used to facilitate doing work outside of an HTTP request/response."""

    def __init__(self, app: flask.app.Flask):
        self.app = app

    def process_not_started_process_instances(self) -> None:
        """Since this runs in a scheduler, we need to specify the app context as well."""
        with self.app.app_context():
            ProcessInstanceLockService.set_thread_local_locking_context("bg:notstarted")
            ProcessInstanceService.do_waiting(ProcessInstanceStatus.not_started.value)

    def process_waiting_process_instances(self) -> None:
        """Since this runs in a scheduler, we need to specify the app context as well."""
        with self.app.app_context():
            ProcessInstanceLockService.set_thread_local_locking_context("bg:waiting")
            ProcessInstanceService.do_waiting(ProcessInstanceStatus.waiting.value)

    def process_running_process_instances(self) -> None:
        """Since this runs in a scheduler, we need to specify the app context as well."""
        with self.app.app_context():
            ProcessInstanceLockService.set_thread_local_locking_context("bg:running")
            ProcessInstanceService.do_waiting(ProcessInstanceStatus.running.value)

    def process_user_input_required_process_instances(self) -> None:
        """Since this runs in a scheduler, we need to specify the app context as well."""
        with self.app.app_context():
            ProcessInstanceLockService.set_thread_local_locking_context("bg:userinput")
            ProcessInstanceService.do_waiting(ProcessInstanceStatus.user_input_required.value)

    def process_message_instances_with_app_context(self) -> None:
        """Since this runs in a scheduler, we need to specify the app context as well."""
        with self.app.app_context():
            ProcessInstanceLockService.set_thread_local_locking_context("bg:messages")
            MessageService.correlate_all_message_instances(execution_mode="synchronous")

    def remove_stale_locks(self) -> None:
        """If something has been locked for a certain amount of time it is probably stale so unlock it."""
        with self.app.app_context():
            ProcessInstanceLockService.remove_stale_locks()

    def process_future_tasks(self) -> None:
        """Timer related tasks go in the future_task table.

        Celery is not great at scheduling things in the distant future. So this function periodically checks the future_task
        table and puts tasks into the queue that are imminently ready to run. Imminently is configurable and defaults to those
        that are 5 minutes away or less.
        """

        with self.app.app_context():
            future_task_lookahead_in_seconds = self.app.config[
                "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_FUTURE_TASK_LOOKAHEAD_IN_SECONDS"
            ]
            self.__class__.do_process_future_tasks(future_task_lookahead_in_seconds)

    @classmethod
    def do_process_future_tasks(cls, future_task_lookahead_in_seconds: int) -> None:
        future_tasks = cls.imminent_future_tasks(future_task_lookahead_in_seconds)
        for future_task in future_tasks:
            process_instance = (
                ProcessInstanceModel.query.join(TaskModel, TaskModel.process_instance_id == ProcessInstanceModel.id)
                .filter(TaskModel.guid == future_task.guid)
                .first()
            )
            if process_instance and process_instance.allowed_to_run():
                queue_future_task_if_appropriate(
                    process_instance, eta_in_seconds=future_task.run_at_in_seconds, task_guid=future_task.guid
                )
            else:
                # if we are not allowed to run the process instance, we should not keep processing the future task
                future_task.archived_for_process_instance_status = True
                db.session.add(future_task)
                db.session.commit()

    @classmethod
    def imminent_future_tasks(cls, future_task_lookahead_in_seconds: int) -> list[FutureTaskModel]:
        lookahead = time.time() + future_task_lookahead_in_seconds
        future_tasks: list[FutureTaskModel] = FutureTaskModel.query.filter(
            and_(
                FutureTaskModel.completed == False,  # noqa: E712
                FutureTaskModel.archived_for_process_instance_status == False,  # noqa: E712
                FutureTaskModel.run_at_in_seconds < lookahead,
                or_(
                    FutureTaskModel.queued_to_run_at_in_seconds != FutureTaskModel.run_at_in_seconds,
                    FutureTaskModel.queued_to_run_at_in_seconds == None,  # noqa: E711
                ),
            )
        ).all()
        return future_tasks

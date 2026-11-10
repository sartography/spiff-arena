import time

import flask
from flask import current_app
from sqlalchemy import and_
from sqlalchemy import or_

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_future_task_if_appropriate,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_event_service import ProcessInstanceEventService
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService

# A process instance whose lock goes stale this many times within the window is put into error.
MAX_STALE_LOCK_STRIKES = 3
STALE_LOCK_STRIKES_WINDOW_IN_SECONDS = 60 * 60


class ProcessInstanceRunLostError(Exception):
    pass


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
            self.__class__.do_remove_stale_locks()

    @classmethod
    def do_remove_stale_locks(cls) -> None:
        """Remove stale locks, and queue their process instances again since the run that held the lock is gone.

        A lock goes stale when its holder dies or cannot reach the database to release it. Background jobs are stopped
        before their lock can go stale (see the time limits in process_instance_task.py), so the holder is not running.
        A process instance that keeps losing its run this way is put into error instead of being run forever.
        """
        for stale_lock in ProcessInstanceLockService.stale_locks():
            try:
                if ProcessInstanceLockService.remove_stale_lock(stale_lock):
                    cls._run_again_after_stale_lock(stale_lock.process_instance_id)
                db.session.commit()
            except Exception:
                # the lock is still there and stale, so the next pass tries again
                db.session.rollback()
                current_app.logger.exception(f"Failed to remove stale lock for process instance {stale_lock.process_instance_id}")

    @classmethod
    def _run_again_after_stale_lock(cls, process_instance_id: int) -> None:
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
        if process_instance is None or process_instance.status not in ProcessInstanceModel.active_statuses():
            return
        ProcessInstanceEventService.add_event_to_process_instance(
            process_instance, ProcessInstanceEventType.process_instance_lock_expired.value
        )
        recent_expired_lock_count = ProcessInstanceEventModel.query.filter(
            ProcessInstanceEventModel.process_instance_id == process_instance_id,
            ProcessInstanceEventModel.event_type == ProcessInstanceEventType.process_instance_lock_expired.value,
            ProcessInstanceEventModel.timestamp > time.time() - STALE_LOCK_STRIKES_WINDOW_IN_SECONDS,
        ).count()
        if recent_expired_lock_count < MAX_STALE_LOCK_STRIKES:
            queue_process_instance_if_appropriate(process_instance)
            return
        error = ProcessInstanceRunLostError(
            f"The last {recent_expired_lock_count} runs of this process instance died or ran for too long."
        )
        ProcessInstanceEventService.add_event_to_process_instance(
            process_instance, ProcessInstanceEventType.process_instance_error.value, exception=error
        )
        ErrorHandlingService.handle_error(process_instance, error)

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

import time
import traceback
from typing import Any

from flask import g
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_error_detail import ProcessInstanceErrorDetailModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_migration_detail import ProcessInstanceMigrationDetailDict
from spiffworkflow_backend.models.process_instance_migration_detail import ProcessInstanceMigrationDetailModel
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.logging_service import LoggingService


class ProcessInstanceTmpService:
    """Temporary service to hold methods that should eventually be moved to ProcessInstanceService.

    These methods cannot live there due to circular import issues with the ProcessInstanceProcessor.
    """

    # TODO: move to process_instance_service once we clean it and the processor up
    @classmethod
    def add_event_to_process_instance(
        cls,
        process_instance: ProcessInstanceModel,
        event_type: str,
        task_guid: str | None = None,
        user: UserModel | None = None,
        exception: Exception | None = None,
        timestamp: float | None = None,
        add_to_db_session: bool | None = True,
        migration_details: ProcessInstanceMigrationDetailDict | None = None,
        log_event: bool = True,
    ) -> tuple[ProcessInstanceEventModel, ProcessInstanceErrorDetailModel | None]:
        if user is None and hasattr(g, "user") and g.user:
            user = g.user
        if timestamp is None:
            timestamp = time.time()

        process_instance_event = ProcessInstanceEventModel(
            process_instance_id=process_instance.id, event_type=event_type, timestamp=timestamp
        )
        if user is not None:
            process_instance_event.user = user
        if task_guid:
            process_instance_event.task_guid = task_guid

        if add_to_db_session:
            db.session.add(process_instance_event)

        log_extras: dict[str, Any] = {"task_id": task_guid}

        process_instance_error_detail = None
        if exception is not None:
            # NOTE: I tried to move this to its own method but
            # est_unlocks_if_an_exception_is_thrown_with_a__dequeued_process_instance
            # gave sqlalchemy rollback errors. I could not figure out why so went back to this.
            #
            # truncate to avoid database errors on large values. We observed that text in mysql is 65K.
            stacktrace = traceback.format_exc().split("\n")
            message = str(exception)[0:1023]

            task_line_number = None
            task_line_contents = None
            task_trace = None
            task_offset = None

            # check for the class name string for ApiError to avoid circular imports
            if isinstance(exception, WorkflowTaskException) or (
                exception.__class__.__name__ == "ApiError" and exception.error_code == "task_error"  # type: ignore
            ):
                task_line_number = exception.line_number  # type: ignore
                error_line = exception.error_line  # type: ignore
                task_line_contents = None if error_line is None else error_line[0:255]
                task_trace = exception.task_trace  # type: ignore
                task_offset = exception.offset  # type: ignore

            process_instance_error_detail = ProcessInstanceErrorDetailModel(
                process_instance_event=process_instance_event,
                message=message,
                stacktrace=stacktrace,
                task_line_number=task_line_number,
                task_line_contents=task_line_contents,
                task_trace=task_trace,
                task_offset=task_offset,
            )

            log_extras["error_info"] = {
                "trace": stacktrace,
                "line_number": task_line_number,
                "line_offset": task_offset,
                "line_content": task_line_contents,
            }

            if add_to_db_session:
                db.session.add(process_instance_error_detail)

        if log_event:
            # Some events need to be logged elsewhere so that all required info can be included
            LoggingService.log_event(event_type, log_extras)

        if migration_details is not None:
            pi_detail = cls.add_process_instance_migration_detail(process_instance_event, migration_details)
            if add_to_db_session:
                db.session.add(pi_detail)

        return (process_instance_event, process_instance_error_detail)

    @classmethod
    def add_process_instance_migration_detail(
        cls, process_instance_event: ProcessInstanceEventModel, migration_details: ProcessInstanceMigrationDetailDict
    ) -> ProcessInstanceMigrationDetailModel:
        pi_detail = ProcessInstanceMigrationDetailModel(
            process_instance_event=process_instance_event,
            initial_git_revision=migration_details["initial_git_revision"],
            target_git_revision=migration_details["target_git_revision"],
            initial_bpmn_process_hash=migration_details["initial_bpmn_process_hash"],
            target_bpmn_process_hash=migration_details["target_bpmn_process_hash"],
        )
        return pi_detail

    @staticmethod
    def is_enqueued_to_run_in_the_future(process_instance: ProcessInstanceModel) -> bool:
        queue_entry = (
            db.session.query(ProcessInstanceQueueModel)
            .filter(ProcessInstanceQueueModel.process_instance_id == process_instance.id)
            .first()
        )

        if queue_entry is None:
            return False

        current_time = round(time.time())
        return queue_entry.run_at_in_seconds > current_time

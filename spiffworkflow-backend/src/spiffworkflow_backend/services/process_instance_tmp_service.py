import logging
import time
import traceback

from flask import g
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_error_detail import ProcessInstanceErrorDetailModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel


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
        user_id: int | None = None,
        exception: Exception | None = None,
        timestamp: float | None = None,
        add_to_db_session: bool | None = True,
    ) -> tuple[ProcessInstanceEventModel, ProcessInstanceErrorDetailModel | None]:
        if user_id is None and hasattr(g, "user") and g.user:
            user_id = g.user.id
        if timestamp is None:
            timestamp = time.time()

        process_instance_event = ProcessInstanceEventModel(
            process_instance_id=process_instance.id, event_type=event_type, timestamp=timestamp, user_id=user_id
        )
        if task_guid:
            process_instance_event.task_guid = task_guid

        if add_to_db_session:
            db.session.add(process_instance_event)

        process_instance_error_detail = None
        if exception is not None:
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

            if add_to_db_session:
                db.session.add(process_instance_error_detail)

        spiff_logger = logging.getLogger("spiff")
        spiff_logger.info("Added event", extra={"__spiff_data": process_instance_event.loggable_event()})
        
        return (process_instance_event, process_instance_error_detail)

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

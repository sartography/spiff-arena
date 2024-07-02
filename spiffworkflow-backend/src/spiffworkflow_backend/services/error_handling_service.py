from flask import current_app
from flask import g

from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class ErrorHandlingService:
    MESSAGE_NAME = "SystemErrorMessage"

    @classmethod
    def handle_error(cls, process_instance: ProcessInstanceModel, error: Exception) -> None:
        """On unhandled exceptions, set instance.status based on model.fault_or_suspend_on_exception."""
        fault_or_suspend_on_exception = "fault"
        exception_notification_addresses = []
        try:
            process_model = ProcessModelService.get_process_model(process_instance.process_model_identifier)
            fault_or_suspend_on_exception = process_model.fault_or_suspend_on_exception
            exception_notification_addresses = process_model.exception_notification_addresses
        except ProcessEntityNotFoundError:
            pass

        cls._update_process_instance_in_database(process_instance, fault_or_suspend_on_exception)

        # Second, send a bpmn message out, but only if an exception notification address is provided
        # This will create a new Send Message with correlation keys on the recipients and the message
        # body.
        if len(exception_notification_addresses) > 0:
            try:
                cls._handle_system_notification(error, process_instance, exception_notification_addresses)
            except Exception as e:
                # hmm... what to do if a notification method fails. Probably log, at least
                current_app.logger.error(e)

    @classmethod
    def _update_process_instance_in_database(
        cls, process_instance: ProcessInstanceModel, fault_or_suspend_on_exception: str
    ) -> None:
        if process_instance.persistence_level == "none":
            return

        # First, suspend or fault the instance
        if fault_or_suspend_on_exception == "suspend":
            cls._set_instance_status(
                process_instance,
                ProcessInstanceStatus.suspended.value,
            )
        else:
            # fault is the default
            cls._set_instance_status(
                process_instance,
                ProcessInstanceStatus.error.value,
            )

        db.session.commit()

    @classmethod
    def _handle_system_notification(
        cls,
        error: Exception,
        process_instance: ProcessInstanceModel,
        exception_notification_addresses: list,
    ) -> None:
        """Send a BPMN Message - which may kick off a waiting process."""

        # importing here to avoid circular imports since these imports are only needed here at runtime.
        # we were not able to figure out which specific import was causing the issue.
        from spiffworkflow_backend.models.message_instance import MessageInstanceModel
        from spiffworkflow_backend.services.message_service import MessageService

        message_text = (
            f"There was an exception running process model {process_instance.process_model_identifier} for instance"
            f" {process_instance.id}.\nOriginal Error:\n{error.__repr__()}"
        )
        message_payload = {
            "message_text": message_text,
            "recipients": exception_notification_addresses,
        }
        user_id = None
        if "user" in g:
            user_id = g.user.id
        else:
            user_id = process_instance.process_initiator_id

        message_instance = MessageInstanceModel(
            message_type="send",
            name=ErrorHandlingService.MESSAGE_NAME,
            payload=message_payload,
            user_id=user_id,
        )
        db.session.add(message_instance)
        db.session.commit()
        MessageService.correlate_send_message(message_instance)

    @classmethod
    def _set_instance_status(cls, process_instance: ProcessInstanceModel, status: str) -> None:
        process_instance.status = status
        db.session.add(process_instance)
        if status == ProcessInstanceStatus.suspended.value:
            ProcessInstanceTmpService.add_event_to_process_instance(
                process_instance, ProcessInstanceEventType.process_instance_suspended_for_error.value, add_to_db_session=True
            )

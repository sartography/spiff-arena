"""Error_handling_service."""
import json
from typing import Union

from flask import current_app
from flask import g
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModelSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class ErrorHandlingService:
    """ErrorHandlingService."""

    MESSAGE_NAME = "SystemErrorMessage"

    @staticmethod
    def set_instance_status(instance_id: int, status: str) -> None:
        """Set_instance_status."""
        instance = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == instance_id)
            .first()
        )
        if instance:
            instance.status = status
            db.session.commit()

    def handle_error(
        self, _processor: ProcessInstanceProcessor, _error: Union[ApiError, Exception]
    ) -> None:
        """On unhandled exceptions, set instance.status based on model.fault_or_suspend_on_exception."""
        process_model = ProcessModelService.get_process_model(
            _processor.process_model_identifier
        )
        # First, suspend or fault the instance
        if process_model.fault_or_suspend_on_exception == "suspend":
            self.set_instance_status(
                _processor.process_instance_model.id,
                ProcessInstanceStatus.suspended.value,
            )
        else:
            # fault is the default
            self.set_instance_status(
                _processor.process_instance_model.id,
                ProcessInstanceStatus.error.value,
            )

        # Second, send a bpmn message out, but only if an exception notification address is provided
        # This will create a new Send Message with correlation keys on the recipients and the message
        # body.
        if len(process_model.exception_notification_addresses) > 0:
            try:
                self.handle_system_notification(_error, process_model, _processor)
            except Exception as e:
                # hmm... what to do if a notification method fails. Probably log, at least
                current_app.logger.error(e)

    @staticmethod
    def handle_system_notification(
            error: Union[ApiError, Exception],
            process_model: ProcessModelInfo,
            _processor: ProcessInstanceProcessor
    ) -> Response:
        """Send a BPMN Message - which may kick off a waiting process. """
        message_text = (
            f"There was an exception running process {process_model.id}.\nOriginal"
            f" Error:\n{error.__repr__()}"
        )
        message_payload = {"message_text": message_text,
                           "recipients": process_model.exception_notification_addresses
                           }
        user_id = None
        if "user" in g:
            user_id = g.user.id
        else:
            user_id = _processor.process_instance_model.process_initiator_id

        message_instance = MessageInstanceModel(
            message_type="send",
            name=ErrorHandlingService.MESSAGE_NAME,
            payload=message_payload,
            user_id=user_id,
        )
        db.session.add(message_instance)
        db.session.commit()
        MessageService.correlate_send_message(message_instance)

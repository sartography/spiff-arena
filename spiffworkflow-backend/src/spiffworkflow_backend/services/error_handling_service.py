"""Error_handling_service."""
import json
from typing import Union

from flask import current_app
from flask import g
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageModel
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

        # Second, call the System Notification Process
        # Note that this isn't the best way to do this.
        # The configs are all in the model.
        # Maybe we can move some of this to the notification process, or dmn tables.
        if len(process_model.exception_notification_addresses) > 0:
            try:
                self.handle_system_notification(_error, process_model)
            except Exception as e:
                # hmm... what to do if a notification method fails. Probably log, at least
                current_app.logger.error(e)

    @staticmethod
    def handle_system_notification(
        error: Union[ApiError, Exception], process_model: ProcessModelInfo
    ) -> Response:
        """Handle_system_notification."""
        recipients = process_model.exception_notification_addresses
        message_text = (
            f"There was an exception running process {process_model.id}.\nOriginal"
            f" Error:\n{error.__repr__()}"
        )
        message_payload = {"message_text": message_text, "recipients": recipients}
        message_identifier = current_app.config[
            "SYSTEM_NOTIFICATION_PROCESS_MODEL_MESSAGE_ID"
        ]
        message_model = MessageModel.query.filter_by(
            identifier=message_identifier
        ).first()
        message_triggerable_process_model = (
            MessageTriggerableProcessModel.query.filter_by(
                message_model_id=message_model.id
            ).first()
        )
        process_instance = MessageService.process_message_triggerable_process_model(
            message_triggerable_process_model,
            message_identifier,
            message_payload,
            g.user,
        )

        return Response(
            json.dumps(ProcessInstanceModelSchema().dump(process_instance)),
            status=200,
            mimetype="application/json",
        )

    # @staticmethod
    # def handle_sentry_notification(_error: ApiError, _recipients: List) -> None:
    #     """SentryHandler."""
    #     ...
    #
    # @staticmethod
    # def handle_email_notification(
    #     processor: ProcessInstanceProcessor,
    #     error: Union[ApiError, Exception],
    #     recipients: List,
    # ) -> None:
    #     """EmailHandler."""
    #     subject = "Unexpected error in app"
    #     if isinstance(error, ApiError):
    #         content = f"{error.message}"
    #     else:
    #         content = str(error)
    #     content_html = content
    #
    #     EmailService.add_email(
    #         subject,
    #         "sender@company.com",
    #         recipients,
    #         content,
    #         content_html,
    #         cc=None,
    #         bcc=None,
    #         reply_to=None,
    #         attachment_files=None,
    #     )
    #
    # @staticmethod
    # def handle_waku_notification(_error: ApiError, _recipients: List) -> Any:
    #     """WakuHandler."""
    #     # class WakuMessage:
    #     #     """WakuMessage."""
    #     #
    #     #     payload: str
    #     #     contentTopic: str  # Optional
    #     #     version: int  # Optional
    #     #     timestamp: int  # Optional


class FailingService:
    """FailingService."""

    @staticmethod
    def fail_as_service() -> None:
        """It fails."""
        raise ApiError(
            error_code="failing_service", message="This is my failing service"
        )

"""Error_handling_service."""
from typing import Any
from typing import List
from typing import Union

from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.services.email_service import EmailService
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
        process_model = ProcessModelService().get_process_model(
            _processor.process_model_identifier, _processor.process_group_identifier
        )
        if process_model.fault_or_suspend_on_exception == "suspend":
            self.set_instance_status(
                _processor.process_instance_model.id,
                ProcessInstanceStatus.suspended.value,
            )
        else:
            # fault is the default
            self.set_instance_status(
                _processor.process_instance_model.id,
                ProcessInstanceStatus.faulted.value,
            )

        if len(process_model.exception_notification_addresses) > 0:
            try:
                # some notification method (waku?)
                self.handle_email_notification(
                    _processor, _error, process_model.exception_notification_addresses
                )
            except Exception as e:
                # hmm... what to do if a notification method fails. Probably log, at least
                print(e)

    @staticmethod
    def hanle_sentry_notification(_error: ApiError, _recipients: List) -> None:
        """SentryHandler."""
        ...

    @staticmethod
    def handle_email_notification(
        processor: ProcessInstanceProcessor,
        error: Union[ApiError, Exception],
        recipients: List,
    ) -> None:
        """EmailHandler."""
        subject = "Unexpected error in app"
        if isinstance(error, ApiError):
            content = f"{error.message}"
        else:
            content = str(error)
        content_html = content

        EmailService.add_email(
            subject,
            "sender@company.com",
            recipients,
            content,
            content_html,
            cc=None,
            bcc=None,
            reply_to=None,
            attachment_files=None,
        )

    @staticmethod
    def handle_waku_notification(_error: ApiError, _recipients: List) -> Any:
        """WakuHandler."""
        # class WakuMessage:
        #     """WakuMessage."""
        #
        #     payload: str
        #     contentTopic: str  # Optional
        #     version: int  # Optional
        #     timestamp: int  # Optional


class FailingService:
    """FailingService."""

    @staticmethod
    def fail_as_service() -> None:
        """It fails."""
        raise ApiError(
            error_code="failing_service", message="This is my failing service"
        )

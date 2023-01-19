"""Background_processing_service."""
import flask

from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class BackgroundProcessingService:
    """Used to facilitate doing work outside of an HTTP request/response."""

    def __init__(self, app: flask.app.Flask):
        """__init__."""
        self.app = app

    def process_waiting_process_instances(self) -> None:
        """Since this runs in a scheduler, we need to specify the app context as well.
        """
        with self.app.app_context():
            ProcessInstanceService.do_waiting()

    def process_message_instances_with_app_context(self) -> None:
        """Since this runs in a scheduler, we need to specify the app context as well.
        """
        with self.app.app_context():
            MessageService.process_message_instances()

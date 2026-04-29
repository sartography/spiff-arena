import unittest

from werkzeug.exceptions import NotFound

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.services.monitoring_service import should_capture_exception_in_sentry


class TestMonitoringService(unittest.TestCase):
    def test_not_found_is_not_captured(self) -> None:
        self.assertFalse(should_capture_exception_in_sentry(NotFound()))

    def test_invalid_token_api_error_is_not_captured(self) -> None:
        self.assertFalse(
            should_capture_exception_in_sentry(
                ApiError(error_code="invalid_token", message="Cannot validate token.", status_code=401)
            )
        )

    def test_missing_process_instance_api_error_is_not_captured(self) -> None:
        self.assertFalse(
            should_capture_exception_in_sentry(
                ApiError(
                    error_code="process_instance_cannot_be_found",
                    message="Process instance cannot be found: 16519",
                    status_code=400,
                )
            )
        )

    def test_not_authorized_error_is_not_captured(self) -> None:
        self.assertFalse(should_capture_exception_in_sentry(NotAuthorizedError()))

    def test_unexpected_api_error_is_captured(self) -> None:
        self.assertTrue(
            should_capture_exception_in_sentry(
                ApiError(error_code="unexpected_workflow_exception", message="Unexpected Workflow Error", status_code=400)
            )
        )

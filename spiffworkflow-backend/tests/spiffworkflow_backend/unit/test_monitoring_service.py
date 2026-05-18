import json
import os
import tempfile
import unittest

from starlette.exceptions import HTTPException as StarletteHTTPException
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import NotFound

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.services.monitoring_service import get_public_version_info_data
from spiffworkflow_backend.services.monitoring_service import should_capture_exception_in_sentry


class Generic404HTTPException(HTTPException):
    code = 404


class Generic500HTTPException(HTTPException):
    code = 500


class TestMonitoringService(unittest.TestCase):
    def test_get_public_version_info_data_returns_minimal_metadata(self) -> None:
        current_dir = os.getcwd()
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                os.chdir(tmp_dir)
                with open("version_info.json", "w", encoding="utf-8") as f:
                    json.dump(
                        {
                            "org.opencontainers.image.version": "main-2026-05-12_17-59-26-6bfb694",
                            "org.opencontainers.image.revision": "6bfb694044244009fe3dd78ae987a9dbae218014",
                            "org.opencontainers.image.created": "2026-05-12T17:59:27.226Z",
                            "org.opencontainers.image.source": "https://github.com/sartography/spiff-arena",
                            "version": "ignored-version",
                            "revision": "ignored-revision",
                            "created": "ignored-created",
                            "git_commit": "ignored-git-commit",
                        },
                        f,
                    )

                self.assertEqual(
                    {
                        "version": "main-2026-05-12_17-59-26-6bfb694",
                        "revision": "6bfb694044244009fe3dd78ae987a9dbae218014",
                        "created": "2026-05-12T17:59:27.226Z",
                    },
                    get_public_version_info_data(),
                )
        finally:
            os.chdir(current_dir)

    def test_not_found_is_not_captured(self) -> None:
        self.assertFalse(should_capture_exception_in_sentry(NotFound()))

    def test_generic_404_http_exception_is_not_captured(self) -> None:
        self.assertFalse(should_capture_exception_in_sentry(Generic404HTTPException()))

    def test_starlette_404_http_exception_is_not_captured(self) -> None:
        self.assertFalse(should_capture_exception_in_sentry(StarletteHTTPException(status_code=404)))

    def test_generic_500_http_exception_is_captured(self) -> None:
        self.assertTrue(should_capture_exception_in_sentry(Generic500HTTPException()))

    def test_starlette_500_http_exception_is_captured(self) -> None:
        self.assertTrue(should_capture_exception_in_sentry(StarletteHTTPException(status_code=500)))

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

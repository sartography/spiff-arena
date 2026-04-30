from unittest.mock import Mock

from flask import Flask
from pytest_mock import MockerFixture

from spiffworkflow_backend.exceptions.api_error import handle_exception


def test_handle_exception_logs_with_logger_exception_in_non_debug_mode(
    app: Flask,
    mocker: MockerFixture,
) -> None:
    app.debug = False
    test_exception = Exception("boom")
    capture_exception_mock = mocker.patch("spiffworkflow_backend.exceptions.api_error.capture_exception", return_value="abc123")
    logger_exception_mock = mocker.patch.object(app.logger, "exception")
    logger_info_mock = mocker.patch.object(app.logger, "info")

    response = handle_exception(app, Mock(), test_exception)

    assert response.status_code == 500
    capture_exception_mock.assert_called_once_with(test_exception)
    logger_exception_mock.assert_called_once_with(test_exception)
    logger_info_mock.assert_not_called()

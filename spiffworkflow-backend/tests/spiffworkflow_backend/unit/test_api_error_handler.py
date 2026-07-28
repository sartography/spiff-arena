from unittest.mock import Mock

from flask import Flask
from lxml.etree import XMLSyntaxError  # type: ignore
from pytest_mock import MockerFixture

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.api_error import handle_exception


def test_from_invalid_xml_includes_file_and_parse_details() -> None:
    parse_error = XMLSyntaxError("Extra content at the end of the document", 1, 28, 27)

    error = ApiError.from_invalid_xml("broken.bpmn", parse_error)

    assert error.error_code == "invalid_xml"
    assert error.message.startswith("'broken.bpmn' is not a valid XML file. ")
    assert "Extra content at the end of the document" in error.message
    assert error.file_name == "broken.bpmn"
    assert error.status_code == 400


def test_handle_exception_captures_exception_without_duplicate_error_log(
    app: Flask,
    mocker: MockerFixture,
) -> None:
    app.debug = False
    test_exception = Exception("boom")
    capture_exception_mock = mocker.patch("spiffworkflow_backend.exceptions.api_error.capture_exception", return_value="abc123")
    logger_exception_mock = mocker.patch.object(app.logger, "exception")
    logger_error_mock = mocker.patch.object(app.logger, "error")
    logger_info_mock = mocker.patch.object(app.logger, "info")

    response = handle_exception(app, Mock(), test_exception)

    assert response.status_code == 500
    capture_exception_mock.assert_called_once_with(test_exception)
    logger_exception_mock.assert_not_called()
    logger_error_mock.assert_not_called()
    logger_info_mock.assert_called_once()
    assert "Captured exception in Sentry" in logger_info_mock.call_args.args[0]

"""Unit tests for deferred API logging functionality."""

from typing import Any
from unittest.mock import patch

import pytest
from flask import Flask
from flask import g

from spiffworkflow_backend.models.api_log_model import APILogModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.utils.api_logging import _log_queue
from spiffworkflow_backend.utils.api_logging import _process_log_queue
from spiffworkflow_backend.utils.api_logging import _queue_api_log_entry
from spiffworkflow_backend.utils.api_logging import log_api_interaction
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestDeferredAPILogging(BaseTest):
    """Test cases for the deferred API logging implementation."""

    def test_decorator_respects_config_setting(self, app: Flask) -> None:
        """Test that the decorator only logs when enabled."""

        @log_api_interaction
        def test_function() -> tuple[dict[str, str], int]:
            return {"result": "success"}, 200

        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Test with logging disabled (default)
            with app.test_request_context("/test", method="POST"):
                result = test_function()
                assert result == ({"result": "success"}, 200)

            # Should not create any logs when disabled
            logs = db.session.query(APILogModel).count()
            assert logs == 0

    def test_decorator_creates_log_when_enabled(self, app: Flask) -> None:
        """Test that the decorator creates logs when enabled."""

        @log_api_interaction
        def test_function() -> tuple[dict[str, str], int]:
            return {"result": "success"}, 200

        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Enable API logging
            app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = True
            # Note: setup_deferred_logging is already called during app creation

            try:
                with app.test_request_context("/test", method="POST", json={"input": "data"}):
                    result = test_function()
                    assert result == ({"result": "success"}, 200)

                    # Process any queued logs (simulating teardown)
                    if hasattr(g, "has_pending_api_logs") and g.has_pending_api_logs:
                        _process_log_queue()

                # Should create a log entry
                logs = db.session.query(APILogModel).all()
                assert len(logs) == 1

                log = logs[0]
                assert log.endpoint == "/test"
                assert log.method == "POST"
                assert log.status_code == 200
                assert log.request_body == {"input": "data"}
                assert log.response_body == {"result": "success"}
                assert log.duration_ms >= 0
            finally:
                app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = False

    def test_decorator_logs_exceptions(self, app: Flask) -> None:
        """Test that the decorator logs when the decorated function raises exceptions."""

        @log_api_interaction
        def test_function() -> None:
            raise ValueError("Test error")

        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Enable API logging
            app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = True
            # Note: setup_deferred_logging is already called during app creation

            try:
                with app.test_request_context("/test", method="GET"):
                    with pytest.raises(ValueError, match="Test error"):
                        test_function()

                    # Process any queued logs
                    if hasattr(g, "has_pending_api_logs") and g.has_pending_api_logs:
                        _process_log_queue()

                # Should still create a log entry for the failed request
                logs = db.session.query(APILogModel).all()
                assert len(logs) == 1

                log = logs[0]
                assert log.endpoint == "/test"
                assert log.method == "GET"
                assert log.status_code == 500  # Default error status
                assert log.duration_ms >= 0
            finally:
                app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = False

    def test_decorator_extracts_api_error_details(self, app: Flask) -> None:
        """Test that the decorator extracts details from API errors."""
        from spiffworkflow_backend.exceptions.api_error import ApiError

        @log_api_interaction
        def test_function() -> None:
            error = ApiError("TEST001", "Test error message", status_code=422)
            raise error

        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Enable API logging
            app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = True
            # Note: setup_deferred_logging is already called during app creation

            try:
                with app.test_request_context("/test", method="POST"):
                    with pytest.raises(ApiError):
                        test_function()

                    # Process any queued logs
                    if hasattr(g, "has_pending_api_logs") and g.has_pending_api_logs:
                        _process_log_queue()

                # Should create a log entry with API error details
                logs = db.session.query(APILogModel).all()
                assert len(logs) == 1

                log = logs[0]
                assert log.status_code == 422
                assert log.response_body is not None  # Should contain error details
            finally:
                app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = False

    def test_process_instance_id_extraction(self, app: Flask) -> None:
        """Test extraction of process_instance_id from various sources."""

        @log_api_interaction
        def test_function_with_kwargs(process_instance_id: int | None = None) -> tuple[dict[str, dict[str, int]], int]:
            return {"process_instance": {"id": 456}}, 200

        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Enable API logging
            app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = True
            # Note: setup_deferred_logging is already called during app creation

            try:
                with app.test_request_context("/test"):
                    # Test extraction from kwargs
                    test_function_with_kwargs(process_instance_id=123)

                    # Process any queued logs
                    if hasattr(g, "has_pending_api_logs") and g.has_pending_api_logs:
                        _process_log_queue()

                logs = db.session.query(APILogModel).all()
                assert len(logs) == 1

                log = logs[0]
                # Should prefer response body over kwargs (456 vs 123)
                assert log.process_instance_id == 456
            finally:
                app.config["SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED"] = False

    def test_queue_processing_outside_flask_context(self, app: Flask) -> None:
        """Test that queueing works outside Flask request context."""
        with app.app_context():
            # Clear existing logs and queue
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Clear the queue
            while not _log_queue.empty():
                _log_queue.get_nowait()

            # Create a log entry outside request context
            log_entry = APILogModel(endpoint="/test", method="POST", status_code=200, duration_ms=100)

            # This should process immediately since we're outside Flask context
            _queue_api_log_entry(log_entry)

            # Should have been processed immediately
            logs = db.session.query(APILogModel).all()
            assert len(logs) == 1
            assert logs[0].endpoint == "/test"

    def test_batch_log_processing(self, app: Flask) -> None:
        """Test that multiple queued entries are processed in batch."""
        with app.app_context():
            # Clear existing logs
            db.session.query(APILogModel).delete()
            db.session.commit()

            # Clear the queue
            while not _log_queue.empty():
                _log_queue.get_nowait()

            # Add multiple entries to queue
            for i in range(3):
                log_entry = APILogModel(endpoint=f"/test{i}", method="GET", status_code=200, duration_ms=50 + i)
                _log_queue.put(log_entry)

            # Process the queue
            _process_log_queue()

            # All entries should be committed
            logs = db.session.query(APILogModel).all()
            assert len(logs) == 3

            endpoints = [log.endpoint for log in logs]
            assert "/test0" in endpoints
            assert "/test1" in endpoints
            assert "/test2" in endpoints

    def test_teardown_handler_setup(self, app: Flask) -> None:
        """Test that setup_deferred_logging properly registers teardown handler."""
        # Note: setup_deferred_logging is already called during app creation
        # so we just test the integration by simulating the teardown process

        # Check that a teardown handler was registered
        # Flask doesn't expose teardown handlers directly, but we can test
        # the integration by simulating the process
        with app.app_context():
            with app.test_request_context("/test"):
                # Set the flag that indicates pending logs
                g.has_pending_api_logs = True

                # Create a mock log entry in the queue
                log_entry = APILogModel(endpoint="/teardown_test", method="POST", status_code=201, duration_ms=75)
                _log_queue.put(log_entry)

                # Manually call what the teardown handler would do
                if hasattr(g, "has_pending_api_logs") and g.has_pending_api_logs:
                    _process_log_queue()

            # Verify the log was processed
            logs = db.session.query(APILogModel).filter_by(endpoint="/teardown_test").all()
            assert len(logs) == 1
            assert logs[0].status_code == 201

    @patch("spiffworkflow_backend.utils.api_logging.logger")
    def test_error_handling_in_log_processing(self, mock_logger: Any, app: Flask) -> None:
        """Test error handling when log processing fails."""
        with app.app_context():
            # Create a valid log entry but mock db.session.commit to raise an exception
            test_entry = APILogModel(endpoint="/error_test", method="GET", status_code=200, duration_ms=100)

            # Mock db.session.commit to raise an exception
            with patch("spiffworkflow_backend.models.db.db.session.commit", side_effect=Exception("DB Error")):
                _log_queue.put(test_entry)
                _process_log_queue()

                # Should log the error
                mock_logger.error.assert_called()
                call_args = mock_logger.error.call_args[0][0]
                assert "Failed to commit API log entries" in call_args

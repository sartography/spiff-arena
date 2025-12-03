import functools
import logging
import threading
import time
from collections.abc import Callable
from queue import Empty
from queue import Queue
from typing import Any

from flask import Flask
from flask import Response
from flask import current_app
from flask import g
from flask import has_request_context
from flask import request

from spiffworkflow_backend.models.api_log_model import APILogModel
from spiffworkflow_backend.models.db import db

logger = logging.getLogger(__name__)

# Thread-safe queue for deferred API log entries
_log_queue: Queue[APILogModel] = Queue()
_log_worker_started = False
_log_worker_lock = threading.Lock()


def _process_log_queue() -> None:
    """Process queued API log entries in batches."""
    entries_to_commit = []

    # Collect all pending entries
    while not _log_queue.empty():
        try:
            entry = _log_queue.get_nowait()
            entries_to_commit.append(entry)
        except Empty:
            break

    if entries_to_commit:
        try:
            # Use a new session to avoid transaction conflicts
            for entry in entries_to_commit:
                db.session.add(entry)
            db.session.commit()
            logger.debug(f"Committed {len(entries_to_commit)} API log entries")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to commit API log entries: {e}")


def _queue_api_log_entry(log_entry: APILogModel) -> None:
    """Queue an API log entry for deferred processing."""
    _log_queue.put(log_entry)

    # Try to mark that we have pending logs for this request context
    if has_request_context():  # type: ignore[no-untyped-call]
        try:
            g.has_pending_api_logs = True
        except RuntimeError:
            # Fallback: process immediately if we can't set the flag
            logger.debug("Processing API log immediately - couldn't set g flag")
            _process_log_queue()
    else:
        # Outside Flask request context (like in tests), process logs immediately
        logger.debug("Processing API log immediately - outside Flask request context")
        _process_log_queue()


def setup_deferred_logging(app: Flask) -> None:
    """Set up teardown handlers for deferred API logging."""

    @app.teardown_appcontext
    def process_pending_logs(error: Exception | None) -> None:
        """Process any pending API logs after the request context ends."""
        if hasattr(g, "has_pending_api_logs") and g.has_pending_api_logs:
            _process_log_queue()


def log_api_interaction(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        # Check if API logging is enabled
        if not current_app.config.get("SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED", False):
            return func(*args, **kwargs)

        start_time = time.time()

        # Capture request details
        endpoint = ""
        method = ""
        request_body = None

        if request:
            try:
                endpoint = request.path
                method = request.method
                request_body = request.get_json(silent=True)
            except RuntimeError:
                # Working outside of request context
                pass
            except Exception:
                request_body = None

        status_code = 500
        response_body = None
        process_instance_id = None
        response = None

        try:
            response = func(*args, **kwargs)
        except Exception as e:
            # If an exception occurs, we try to get the status code from it if it's an API error
            if hasattr(e, "status_code"):
                status_code = e.status_code
            if hasattr(e, "to_dict"):
                response_body = e.to_dict()
            raise e
        finally:
            duration_ms = int((time.time() - start_time) * 1000)

            if response:
                if isinstance(response, Response):
                    status_code = response.status_code
                    try:
                        if response.is_json:
                            response_body = response.get_json()
                    except Exception:
                        # We might fail to parse JSON if the response is not actually JSON
                        # despite the header, or some other issue. We'll just skip the body.
                        logger.warning("Failed to parse response body as JSON", exc_info=True)
                        pass
                elif isinstance(response, tuple) and len(response) >= 2:
                    # Handle tuple responses like (data, status_code) or (data, status_code, headers)
                    response_body = response[0]
                    if isinstance(response[1], int):
                        status_code = response[1]
                else:
                    # Handle other response types - assume it's the response body
                    response_body = response

            # Extract process_instance_id if available in response
            if response_body and isinstance(response_body, dict):
                if "process_instance" in response_body and isinstance(response_body["process_instance"], dict):
                    process_instance_id = response_body["process_instance"].get("id")
                elif "id" in response_body:
                    # Sometimes the response IS the process instance
                    process_instance_id = response_body.get("id")

            # If not found in response, check if it was in the args (e.g. for run)
            if not process_instance_id:
                if "process_instance_id" in kwargs:
                    process_instance_id = kwargs["process_instance_id"]

            log_entry = APILogModel(
                endpoint=endpoint,
                method=method,
                request_body=request_body,
                response_body=response_body,
                status_code=status_code,
                process_instance_id=process_instance_id,
                duration_ms=duration_ms,
            )
            # Queue the log entry for deferred processing instead of immediate commit
            _queue_api_log_entry(log_entry)

        return response

    return wrapper

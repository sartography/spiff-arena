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


def _extract_request_context() -> dict[str, Any]:
    """Helper to extract common request details."""
    endpoint = ""
    method = ""
    request_body = None
    query_params = None

    if request:
        try:
            endpoint = request.path
            method = request.method
            request_body = request.get_json(silent=True)
            query_params = dict(request.args)
        except RuntimeError:
            pass
        except Exception:
            request_body = None

    return {"endpoint": endpoint, "method": method, "request_body": request_body, "query_params": query_params}


def _create_log_entry_final(
    start_time: float,
    response: Any = None,
    exception: Exception | None = None,
    kwargs: dict[str, Any] | None = None,
) -> None:
    """Consolidated helper to create and queue log entries from response or exception."""
    context = _extract_request_context()
    status_code = 500
    response_body = None

    if exception:
        if hasattr(exception, "status_code"):
            status_code = exception.status_code
        if hasattr(exception, "to_dict"):
            response_body = exception.to_dict()
        else:
            response_body = {"fabricated_response_body_from_exception": f"{exception.__class__.__name__}: {str(exception)}"}
    elif response:
        if isinstance(response, Response):
            status_code = response.status_code
            try:
                if response.is_json:
                    response_body = response.get_json()
            except Exception:
                logger.warning("Failed to parse response body as JSON", exc_info=True)
        elif isinstance(response, tuple) and len(response) >= 2:
            response_body = response[0]
            if isinstance(response[1], int):
                status_code = response[1]
        else:
            response_body = response
            # If no status code was derived from response object, assume 200 for successful returns
            if status_code == 500:
                status_code = 200

    process_instance_id = None
    if response_body and isinstance(response_body, dict):
        if "process_instance" in response_body and isinstance(response_body["process_instance"], dict):
            process_instance_id = response_body["process_instance"].get("id")
        elif "id" in response_body:
            process_instance_id = response_body.get("id")

    if not process_instance_id and kwargs and "process_instance_id" in kwargs:
        process_instance_id = kwargs["process_instance_id"]

    duration_ms = int((time.time() - start_time) * 1000)

    log_entry = APILogModel(
        endpoint=context["endpoint"],
        method=context["method"],
        request_body=context["request_body"],
        query_params=context["query_params"],
        response_body=response_body,
        status_code=status_code,
        process_instance_id=process_instance_id,
        duration_ms=duration_ms,
    )
    _queue_api_log_entry(log_entry)

    if request:
        g.api_log_created = True


def setup_global_api_logging(app: Flask) -> None:
    """Set up global API logging for all endpoints."""

    # Check config at setup time to avoid registering hooks if not needed
    if not app.config.get("SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED", False):
        return

    if not app.config.get("SPIFFWORKFLOW_BACKEND_API_LOG_ALL_ENDPOINTS", False):
        return

    @app.before_request
    def start_timer() -> None:
        g.api_log_start_time = time.time()

    @app.after_request
    def log_request(response: Response) -> Response:
        # Runtime check in case config allows runtime changes (unlikely) or just safety
        if not current_app.config.get("SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED", False):
            return response

        if not current_app.config.get("SPIFFWORKFLOW_BACKEND_API_LOG_ALL_ENDPOINTS", False):
            return response

        # Skip if this request was already logged by the decorator
        if hasattr(g, "api_log_created") and g.api_log_created:
            return response

        try:
            start_time = getattr(g, "api_log_start_time", time.time())
            _create_log_entry_final(start_time, response=response)
        except Exception:
            logger.exception("Failed to globally log API interaction")

        return response


def log_api_interaction(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if not current_app.config.get("SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED", False):
            return func(*args, **kwargs)

        start_time = time.time()

        try:
            response = func(*args, **kwargs)
            _create_log_entry_final(start_time, response=response, kwargs=kwargs)
            return response
        except Exception as e:
            _create_log_entry_final(start_time, exception=e, kwargs=kwargs)
            raise e

    return wrapper

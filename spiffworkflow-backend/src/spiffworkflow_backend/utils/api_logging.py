import functools
import time
from typing import Any
from typing import Callable

from flask import request
from flask import Response

from spiffworkflow_backend.models.api_log_model import APILogModel
from spiffworkflow_backend.models.db import db


def log_api_interaction(func: Callable) -> Callable:
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        
        # Capture request details
        endpoint = request.path
        method = request.method
        try:
            request_body = request.get_json(silent=True)
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
                        pass
                else:
                    # Handle cases where response might not be a Flask Response object immediately
                    # (though in controllers it usually is)
                    pass

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
                duration_ms=duration_ms
            )
            db.session.add(log_entry)
            db.session.commit()

        return response
    return wrapper

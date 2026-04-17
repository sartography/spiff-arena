import json
import logging
from json import JSONDecodeError
from typing import Any

import requests
import sentry_sdk
from flask import current_app
from flask import g
from security import safe_requests  # type: ignore
from SpiffWorkflow.bpmn import BpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.serializer.helpers.registry import DefaultRegistry  # type: ignore
from SpiffWorkflow.spiff.specs.event_definitions import ErrorEventDefinition  # type: ignore
from SpiffWorkflow.spiff.specs.event_definitions import EscalationEventDefinition
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore
from spiffworkflow_connector_command.command_interface import CommandErrorDict

from spiffworkflow_backend.config import CONNECTOR_PROXY_COMMAND_TIMEOUT
from spiffworkflow_backend.config import HTTP_REQUEST_TIMEOUT_SECONDS
from spiffworkflow_backend.connectors import http_connector
from spiffworkflow_backend.helpers.public_api_urls import build_public_api_v1_url
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.user_service import UserService

logger = logging.getLogger(__name__)


class ConnectorProxyError(Exception):
    pass


class UncaughtServiceTaskError(Exception):
    pass


class Accepted202Exception(Exception):  # noqa N818
    pass


class ServiceTaskErrorDict(CommandErrorDict):
    operator_identifier: str
    status_code: int
    command_response_body: Any


def connector_proxy_url() -> Any:
    return current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL"]


def connector_proxy_api_key_headers() -> dict:
    api_key = current_app.config.get("SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_API_KEY")
    if api_key:
        return {"Spiff-Connector-Proxy-Api-Key": api_key}
    return {}


def connector_proxy_http_logging_enabled() -> bool:
    return bool(current_app.config.get("SPIFFWORKFLOW_BACKEND_LOG_CONNECTOR_PROXY_HTTP", False))


def _format_log_value(value: Any) -> str:
    if value in (None, ""):
        return "<empty>"

    if isinstance(value, str):
        try:
            parsed_value = json.loads(value)
        except (TypeError, ValueError):
            return value
        return json.dumps(parsed_value, indent=2, sort_keys=True, default=str)

    return json.dumps(value, indent=2, sort_keys=True, default=str)


def _redact_sensitive_headers(headers: dict[str, Any] | None) -> dict[str, Any] | None:
    if headers is None:
        return None

    sensitive_header_names = {
        "authorization",
        "proxy-authorization",
        "x-api-key",
        "api-key",
        "apikey",
        "token",
        "secret",
        "password",
        "spiff-connector-proxy-api-key",
    }
    redacted_headers: dict[str, Any] = {}
    for key, value in headers.items():
        if str(key).lower() in sensitive_header_names:
            redacted_headers[key] = "<redacted>"
        else:
            redacted_headers[key] = value

    return redacted_headers


def _log_connector_proxy_request(operator_identifier: str, method: str, url: str, headers: dict[str, Any], body: Any) -> None:
    if not connector_proxy_http_logging_enabled():
        return
    logger.info(
        "Connector proxy request\nOperator: %s\nMethod: %s\nURL: %s\nHeaders:\n%s\nBody:\n%s",
        operator_identifier,
        method,
        url,
        _format_log_value(_redact_sensitive_headers(headers)),
        _format_log_value(body),
    )


def _log_connector_proxy_response(
    operator_identifier: str, method: str, url: str, status_code: int, headers: Any, body: str
) -> None:
    if not connector_proxy_http_logging_enabled():
        return
    response_headers = dict(headers) if headers is not None else None
    logger.info(
        "Connector proxy response\nOperator: %s\nMethod: %s\nURL: %s\nStatus: %s\nHeaders:\n%s\nBody:\n%s",
        operator_identifier,
        method,
        url,
        status_code,
        _format_log_value(_redact_sensitive_headers(response_headers)),
        _format_log_value(body),
    )


def _log_connector_proxy_exception(
    operator_identifier: str, method: str, url: str, headers: dict[str, Any], body: Any, exception: Exception
) -> None:
    if not connector_proxy_http_logging_enabled():
        return
    logger.error(
        "Connector proxy request failed\nOperator: %s\nMethod: %s\nURL: %s\nHeaders:\n%s\nBody:\n%s\nException: %s: %s",
        operator_identifier,
        method,
        url,
        _format_log_value(_redact_sensitive_headers(headers)),
        _format_log_value(body),
        exception.__class__.__name__,
        exception,
    )


class ServiceTaskDelegate:
    @classmethod
    def handle_template_substitutions(cls, value: Any) -> Any:
        if isinstance(value, str):
            secret_prefix = "secret:"  # noqa: S105
            if value.startswith(secret_prefix):
                key = value.removeprefix(secret_prefix)
                secret = SecretService.get_secret(key)
                with sentry_sdk.start_span(op="task", name="decrypt_secret"):
                    return SecretService._decrypt(secret.value)

            file_prefix = "file:"
            if value.startswith(file_prefix):
                file_name = value.removeprefix(file_prefix)
                full_path = FileSystemService.full_path_from_relative_path(file_name)
                with open(full_path) as f:
                    return f.read()

            return SecretService.resolve_possibly_secret_value(value)

        return value

    @classmethod
    def value_with_secrets_replaced(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls.handle_template_substitutions(value)
        if isinstance(value, dict):
            for key, v in value.items():
                value[key] = cls.value_with_secrets_replaced(v)
        return value

    @classmethod
    def get_message_for_status(cls, code: int) -> str:
        msg = f"HTTP Status Code {code}."
        if code == 301:
            msg = "301 (Permanent Redirect) - you may need to use a different URL in this service task."
        if code == 302:
            msg = "302 (Temporary Redirect) - you may need to use a different URL in this service task."
        if code == 400:
            msg = "400 (Bad Request) - The request was received by the service, but it was not understood."
        if code == 401:
            msg = "401 (Unauthorized Error) - this end point requires some form of authentication."
        if code == 403:
            msg = "403 (Forbidden) - The service you called refused to accept the request."
        if code == 404:
            msg = "404 (Not Found) - The service did not find the requested resource."
        if code == 500:
            msg = "500 (Internal Server Error) - The service you called is experiencing technical difficulties."
        if code == 501:
            msg = "501 (Not Implemented) - This service needs to be called with the different method (like POST not GET)."
        return msg

    @classmethod
    def catch_error_codes(cls, spiff_task: SpiffTask, error: Any) -> None:
        task_workflow = spiff_task.workflow
        top_level_workflow = task_workflow.top_workflow
        task_caught_event = False
        for event_definition_class in [ErrorEventDefinition, EscalationEventDefinition]:
            event_definition = event_definition_class(name=error["error_code"], code=error["error_code"])
            bpmn_event = BpmnEvent(event_definition, payload=error, target=task_workflow)
            tasks = task_workflow.get_tasks(catches_event=bpmn_event, state=TaskState.NOT_FINISHED_MASK)
            if len(tasks) == 0:
                tasks = top_level_workflow.get_tasks(catches_event=bpmn_event, state=TaskState.NOT_FINISHED_MASK)
                bpmn_event = BpmnEvent(event_definition, payload=error)
            if len(tasks) > 0:
                top_level_workflow.catch(bpmn_event)
                task_caught_event = True

        if task_caught_event is False:
            message_from_status_code = cls.get_message_for_status(error["status_code"])
            message = [
                f"Received error code '{error['error_code']}' from service '{error['operator_identifier']}'",
                message_from_status_code,
                f"The original message: {error['message']}",
            ]
            raise UncaughtServiceTaskError(" ::: ".join(message))

    @classmethod
    def check_for_errors(
        cls,
        spiff_task: SpiffTask,
        parsed_response: dict,
        status_code: int,
        response_text: str,
        operator_identifier: str,
    ) -> None:
        base_error = None
        if "error" in parsed_response and isinstance(parsed_response["error"], dict) and "error_code" in parsed_response["error"]:
            base_error = parsed_response["error"]
        elif (
            "command_response_version" in parsed_response
            and parsed_response.get("command_response_version", 0) > 1
            and isinstance(parsed_response.get("command_response"), dict)
            and parsed_response["command_response"].get("http_status", 0) >= 300
        ):
            upstream_status = parsed_response["command_response"]["http_status"]
            base_error = {
                "error_code": f"ServiceTaskHttpError{upstream_status}",
                "message": f"Service task received HTTP {upstream_status} from upstream service. Response: {response_text}",
            }
        elif status_code >= 300:
            error_message = ""
            if "error" in parsed_response:
                error_response = parsed_response["error"] or ""
                if isinstance(error_response, list | dict):
                    error_response = json.dumps(error_response)
                else:
                    error_response = str(error_response) if error_response is not None else ""
                error_message += error_response
            if not error_message:
                error_message = response_text
            error_message += " A critical component (The connector proxy) is not responding correctly."
            base_error = {
                "error_code": "ServiceTaskOperatorReturnedBadStatusError",
                "message": error_message,
            }

        if base_error is not None:
            error_dict: ServiceTaskErrorDict = {
                "error_code": base_error["error_code"],
                "message": base_error["message"],
                "operator_identifier": operator_identifier,
                "status_code": status_code,
                "command_response_body": response_text,
            }
            cls.catch_error_codes(spiff_task, error_dict)

    @classmethod
    def call_connector(
        cls, operator_identifier: str, bpmn_params: Any, spiff_task: SpiffTask, process_instance_id: int | None
    ) -> str:
        call_url = f"{connector_proxy_url()}/v1/do/{operator_identifier}"
        request_method = "POST"
        current_app.logger.info(f"Calling connector proxy using connector: {operator_identifier}")
        task_data = spiff_task.data
        with sentry_sdk.start_span(op="connector_by_name", name=operator_identifier):
            with sentry_sdk.start_span(op="call-connector", name=call_url):
                params = {k: cls.value_with_secrets_replaced(v["value"]) for k, v in bpmn_params.items()}
                params["spiff__process_instance_id"] = process_instance_id
                params["spiff__task_id"] = str(spiff_task.id)
                params["spiff__task_data"] = task_data
                params["spiff__callback_url"] = build_public_api_v1_url(
                    current_app.config["SPIFFWORKFLOW_BACKEND_URL"],
                    f"tasks/{process_instance_id}/{spiff_task.id}/callback",
                )
                params = DefaultRegistry().convert(params)
                request_headers = connector_proxy_api_key_headers()
                _log_connector_proxy_request(operator_identifier, request_method, call_url, request_headers, params)
                response_text = ""
                status_code = 0
                parsed_response: dict = {}
                try:
                    if http_connector.does(operator_identifier):
                        proxied_response = http_connector.do(operator_identifier, params)
                    else:
                        proxied_response = requests.post(
                            call_url,
                            json=params,
                            headers=request_headers,
                            timeout=CONNECTOR_PROXY_COMMAND_TIMEOUT,
                        )

                    status_code = proxied_response.status_code
                    response_text = proxied_response.text
                    _log_connector_proxy_response(
                        operator_identifier,
                        request_method,
                        call_url,
                        status_code,
                        proxied_response.headers,
                        response_text,
                    )
                except Exception as exception:
                    _log_connector_proxy_exception(
                        operator_identifier, request_method, call_url, request_headers, params, exception
                    )
                    status_code = status_code or 500
                    parsed_response = {
                        "error": {
                            "error_code": exception.__class__.__name__,
                            "message": str(exception),
                        }
                    }

                if status_code == 202:
                    raise Accepted202Exception()

                if "error" not in parsed_response:
                    try:
                        parsed_response = json.loads(response_text or "{}")
                    except JSONDecodeError:
                        parsed_response = {
                            "error": {
                                "error_code": "ServiceTaskOperatorReturnedInvalidJsonError",
                                "message": response_text,
                            }
                        }

                if "spiff__logs" in parsed_response:
                    for log in parsed_response["spiff__logs"]:
                        current_app.logger.info(f"Log from connector {operator_identifier}: {log}")
                    if "api_response" in parsed_response:
                        parsed_response = parsed_response["api_response"]
                        response_text = json.dumps(parsed_response)

                if "command_response_version" in parsed_response and parsed_response["command_response_version"] > 1:
                    new_response = parsed_response["command_response"]
                    new_response["operator_identifier"] = operator_identifier
                    response_text = json.dumps(new_response)

                cls.check_for_errors(spiff_task, parsed_response, status_code, response_text, operator_identifier)

                if "refreshed_token_set" not in parsed_response:
                    return response_text or "{}"

                secret_key = parsed_response["auth"]
                refreshed_token_set = json.dumps(parsed_response["refreshed_token_set"])
                user_id = g.user.id if UserService.has_user() else None
                SecretService.update_secret(secret_key, refreshed_token_set, user_id)
                return json.dumps(parsed_response["api_response"])


class ServiceTaskDelegateService:
    @staticmethod
    def available_connectors() -> Any:
        try:
            response = safe_requests.get(
                f"{connector_proxy_url()}/v1/commands",
                headers=connector_proxy_api_key_headers(),
                timeout=HTTP_REQUEST_TIMEOUT_SECONDS,
            )

            if response.status_code != 200:
                return []

            parsed_response = json.loads(response.text)
            return parsed_response
        except Exception as e:
            current_app.logger.error(e)
            return []

    @staticmethod
    def authentication_list() -> Any:
        try:
            response = safe_requests.get(
                f"{connector_proxy_url()}/v1/auths",
                headers=connector_proxy_api_key_headers(),
                timeout=HTTP_REQUEST_TIMEOUT_SECONDS,
            )

            if response.status_code != 200:
                return []

            parsed_response = json.loads(response.text)
            return parsed_response
        except Exception as exception:
            raise ConnectorProxyError(exception.__class__.__name__) from exception

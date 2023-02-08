"""ServiceTask_service."""
import json
from typing import Any

import requests
import sentry_sdk
from flask import current_app
from flask import g

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.user_service import UserService


class ConnectorProxyError(Exception):
    """ConnectorProxyError."""


def connector_proxy_url() -> Any:
    """Returns the connector proxy url."""
    return current_app.config["CONNECTOR_PROXY_URL"]


class ServiceTaskDelegate:
    """ServiceTaskDelegate."""

    @staticmethod
    def check_prefixes(value: Any) -> Any:
        """Check_prefixes."""
        if isinstance(value, str):
            secret_prefix = "secret:"  # noqa: S105
            if value.startswith(secret_prefix):
                key = value.removeprefix(secret_prefix)
                secret = SecretService().get_secret(key)
                return secret.value

            file_prefix = "file:"
            if value.startswith(file_prefix):
                file_name = value.removeprefix(file_prefix)
                full_path = FileSystemService.full_path_from_relative_path(file_name)
                with open(full_path) as f:
                    return f.read()

        return value

    @staticmethod
    def get_message_for_status(code):
        """Given a code like 404, return a string like 'The requested resource was not found.'"""
        msg = f'HTTP Status Code {code}.'
        if code == 301:
            msg =  '301 (Permanent Redirect) - you may need to use a different URL in this service task.'
        if code == 302:
            msg =  '302 (Temporary Redirect) - you may need to use a different URL in this service task.'
        if code == 400:
            msg =  '400 (Bad Request) - The request was received by the service, but it was not understood.'
        if code == 401:
            msg =  '401 (Unauthorized Error) - this end point requires some form of authentication.'
        if code == 403:
            msg =  '403 (Forbidden) - The service you called refused to accept the request.'
        if code == 404:
            msg =  '404 (Not Found) - The service did not find the requested resource.'
        if code == 500:
            msg =  '500 (Internal Server Error) - The service you called is experiencing technical difficulties.'
        if code == 501:
            msg =  '501 (Not Implemented) - This service needs to be called with the different method (like POST not GET).'
        return msg

    @staticmethod
    def call_connector(name: str, bpmn_params: Any, task_data: Any) -> str:
        """Calls a connector via the configured proxy."""
        call_url = f"{connector_proxy_url()}/v1/do/{name}"
        with sentry_sdk.start_span(op="call-connector", description=call_url):
            params = {
                k: ServiceTaskDelegate.check_prefixes(v["value"])
                for k, v in bpmn_params.items()
            }
            params["spiff__task_data"] = task_data

            proxied_response = requests.post(call_url, json=params)
            response_text = proxied_response.text
            json_parse_error = None

            if response_text == "":
                response_text = "{}"
            try:
                parsed_response = json.loads(response_text)
            except Exception as e:
                json_parse_error = e
                parsed_response = {}

            if proxied_response.status_code >= 300:
                error = f"Received an unexpected response from the service : "
                error += ServiceTaskDelegate.get_message_for_status(proxied_response.status_code)
                if "error" in parsed_response:
                    error += parsed_response["error"]
                if json_parse_error:
                    error += "A critical component (The connector proxy) is not responding correctly."
                raise ConnectorProxyError(error)
            elif json_parse_error:
                raise ConnectorProxyError( f"There is a problem with this connector: '{name}'. "
                                           f"Responses for connectors must be in JSON format. ")

            if "refreshed_token_set" not in parsed_response:
                return response_text

            secret_key = parsed_response["auth"]
            refreshed_token_set = json.dumps(parsed_response["refreshed_token_set"])
            user_id = g.user.id if UserService.has_user() else None
            SecretService().update_secret(secret_key, refreshed_token_set, user_id)
            return json.dumps(parsed_response["api_response"])



class ServiceTaskService:
    """ServiceTaskService."""

    @staticmethod
    def available_connectors() -> Any:
        """Returns a list of available connectors."""
        try:
            response = requests.get(f"{connector_proxy_url()}/v1/commands")

            if response.status_code != 200:
                return []

            parsed_response = json.loads(response.text)
            return parsed_response
        except Exception as e:
            current_app.logger.error(e)
            return []

    @staticmethod
    def authentication_list() -> Any:
        """Returns a list of available authentications."""
        try:
            response = requests.get(f"{connector_proxy_url()}/v1/auths")

            if response.status_code != 200:
                return []

            parsed_response = json.loads(response.text)
            return parsed_response
        except Exception as exception:
            raise ConnectorProxyError(exception.__class__.__name__) from exception

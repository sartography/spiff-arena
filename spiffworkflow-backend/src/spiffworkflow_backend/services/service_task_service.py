"""ServiceTask_service."""
import json
from typing import Any

import requests
from flask import current_app
from flask import g

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
    def call_connector(name: str, bpmn_params: Any, task_data: Any) -> str:
        """Calls a connector via the configured proxy."""
        params = {
            k: ServiceTaskDelegate.check_prefixes(v["value"])
            for k, v in bpmn_params.items()
        }
        params["spiff__task_data"] = task_data

        proxied_response = requests.post(
            f"{connector_proxy_url()}/v1/do/{name}", json=params
        )

        parsed_response = json.loads(proxied_response.text)

        if "refreshed_token_set" not in parsed_response:
            return proxied_response.text

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

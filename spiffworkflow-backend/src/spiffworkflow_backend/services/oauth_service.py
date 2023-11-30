import base64
import json
from typing import Any

from flask import Flask
from flask import session
from flask_oauthlib.client import OAuth  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.configuration_service import ConfigurationService
from spiffworkflow_backend.services.secret_service import SecretService


class OAuthService:
    @classmethod
    def authentication_list(
        cls,
    ) -> list[dict[str, Any]]:
        return [{"id": f"{k}/OAuth", "parameters": []} for k in cls.authentication_configuration().keys()]

    @staticmethod
    def authentication_configuration() -> Any:
        return ConfigurationService.configuration_for_category("oauth")

    @staticmethod
    def update_authentication_configuration(config: dict[str, Any]) -> None:
        try:
            _ = json.loads(config["value"])
        except Exception as e:
            raise ApiError(
                error_code="invalid_authentication_configuration",
                message=f"The authentication configuration is not valid JSON. {e}",
            ) from e

        return ConfigurationService.update_configuration_for_category("oauth", config)

    @classmethod
    def supported_service(cls, service: str) -> bool:
        return service in cls.authentication_configuration()

    @classmethod
    def remote_app(cls, service: str, token: str | None) -> Any:
        config = cls.authentication_configuration()[service]

        for k in ["consumer_key", "consumer_secret"]:
            if k in config:
                config[k] = SecretService.resolve_possibly_secret_value(config[k])

        if token is not None:
            state = base64.urlsafe_b64encode(bytes(token, "utf-8"))
            config["request_token_params"]["state"] = state

        app = Flask(__name__)
        oauth = OAuth(app)
        remote_app = oauth.remote_app(service, **config)

        @remote_app.tokengetter
        def get_token(token=None):  # type: ignore
            return session[f"{service}_token"]

        return remote_app

    @staticmethod
    def token_from_state(state: str | None) -> str | None:
        if state is not None:
            return base64.urlsafe_b64decode(state).decode("utf-8")
        return None

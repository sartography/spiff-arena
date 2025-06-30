import base64
import json
from typing import Any

from authlib.integrations.flask_client import OAuth

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.configuration_service import ConfigurationService
from spiffworkflow_backend.services.secret_service import SecretService


class AuthlibWrapper:
    def __init__(self, remote_app: Any, state: str | None = None):
        self.remote_app = remote_app
        self.state = state

    def authorize(self, **kwargs: Any) -> Any:
        redirect_uri = kwargs.get("callback")
        return self.remote_app.authorize_redirect(redirect_uri=redirect_uri, state=self.state)

    def authorized_response(self) -> Any:
        return self.remote_app.authorize_access_token()


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
        config = cls.authentication_configuration().get(service, {})

        for k in ["client_id", "client_secret"]:
            if k in config:
                config[k] = SecretService.resolve_possibly_secret_value(config[k])

        state = None
        if token is not None:
            state = base64.urlsafe_b64encode(bytes(token, "utf-8")).decode("utf-8")
            # In flask-oauthlib, state was passed in request_token_params.
            # In authlib, it's passed to authorize_redirect.
            # We remove it from config if it exists, and pass it to our wrapper.
            if "request_token_params" in config:
                config["request_token_params"].pop("state", None)
                if not config["request_token_params"]:
                    del config["request_token_params"]

        oauth = OAuth()  # type: ignore
        remote_app = oauth.register(service, **config)  # type: ignore

        return AuthlibWrapper(remote_app, state=state)

    @staticmethod
    def token_from_state(state: str | None) -> str | None:
        if state is not None:
            return base64.urlsafe_b64decode(state).decode("utf-8")
        return None

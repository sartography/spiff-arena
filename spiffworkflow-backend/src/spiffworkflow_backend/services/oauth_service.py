import base64
from typing import Any

from flask import Flask
from flask import session
from flask_oauthlib.client import OAuth  # type: ignore
from spiffworkflow_backend.services.secret_service import SecretService

# TODO: get this from somewhere dynamic, admins need to edit from the UI
AUTHS = {
    "github": {
        "consumer_key": "SPIFF_SECRET:GITHUB_CONSUMER_KEY",
        "consumer_secret": "SPIFF_SECRET:GITHUB_CONSUMER_SECRET",
        "request_token_params": {"scope": "user:email"},
        "base_url": "https://api.github.com/",
        "request_token_url": None,
        "access_token_method": "POST",
        "access_token_url": "https://github.com/login/oauth/access_token",
        "authorize_url": "https://github.com/login/oauth/authorize",
    },
}


class OAuthService:
    @staticmethod
    def authentication_list() -> list[dict[str, Any]]:
        return [{"id": f"{k}/OAuth", "parameters": []} for k in AUTHS.keys()]

    @staticmethod
    def authentication_configuration() -> dict[str, Any]:
        return AUTHS

    @staticmethod
    def supported_service(service: str) -> bool:
        return service in AUTHS

    @staticmethod
    def remote_app(service: str, token: str | None) -> Any:
        config = AUTHS[service].copy()

        for k in ["consumer_key", "consumer_secret"]:
            if k in config:
                config[k] = SecretService.resolve_possibly_secret_value(config[k])  # type: ignore

        if token is not None:
            state = base64.urlsafe_b64encode(bytes(token, "utf-8"))
            config["request_token_params"]["state"] = state  # type: ignore

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

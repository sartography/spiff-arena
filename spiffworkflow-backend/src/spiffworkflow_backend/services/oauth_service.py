
from spiffworkflow_backend.services.secret_service import SecretService

from typing import Dict, List, Any

from flask import Flask, session
from flask_oauthlib.client import OAuth
from hashlib import sha256
import base64
import time

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
      def authentication_list() -> List[Dict[str, Any]]:
            return [{"id": f"{k}/OAuth", "parameters": []} for k in AUTHS.keys()]

      @staticmethod
      def supported_service(service: str) -> bool:
            return service in AUTHS

      @staticmethod
      def remote_app(service: str, token: str) -> Any:
            config = AUTHS[service].copy()

            for k in ["consumer_key", "consumer_secret"]:
                  if k in config:
                        config[k] = SecretService.resolve_possibly_secret_value(config[k])

            state = base64.urlsafe_b64encode(bytes(token, "utf-8"))
            config["request_token_params"]["state"] = state

            app = Flask(__name__)
            oauth = OAuth(app)
            remote_app = oauth.remote_app(service, **config)

            @remote_app.tokengetter
            def get_token(token=None):
                  return session[f"{service}_token"]
            
            return remote_app

      @staticmethod
      def token_from_state(state: str) -> str:
            return base64.urlsafe_b64decode(state).decode("utf-8")

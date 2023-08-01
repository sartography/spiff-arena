
from spiffworkflow_backend.services.secret_service import SecretService

from typing import Dict, List, Any

from flask import Flask, session
from flask_oauthlib.client import OAuth
from hashlib import sha256
import base64
import time

# TODO: get this from somewhere dynamic, admins need to edit from the UI
# TODO: also don't like the name
# TODO: build non scope request_token_params in remote_app
AUTHS = {
      "airtable": {
            "consumer_key": "SPIFF_SECRET:AIRTABLE_CONSUMER_KEY",
            "consumer_secret": "SPIFF_SECRET:AIRTABLE_CONSUMER_SECRET",
            "request_token_params": {
                  "grant_type": "authorization_code",
                  "scope": "data.records:read schema.bases:read",
            },
            "access_token_params": {
            },
            "base_url": "https://airtable.com/",
            "access_token_method": "POST",
            "access_token_url": "https://airtable.com/oauth2/v1/token",
            "authorize_url": "https://airtable.com/oauth2/v1/authorize",
            #"request_token_url": "https://airtable.com/oauth2/v1/token",
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
      def remote_app(service: str) -> Any: # TODO what is this type
            config = AUTHS[service].copy()

            for k in ["consumer_key", "consumer_secret"]:
                  if k in config:
                        config[k] = SecretService.resolve_possibly_secret_value(config[k])

            transient_config_key = f"{service}_transient_config"
            transient_config = session.pop(transient_config_key, None)
            
            if transient_config is None:
                  now = time.time()
                  code_verifier_hash = sha256(f"oauth_{service}_{config['consumer_secret']}_{now}".encode("utf-8"))
                  code_verifier = code_verifier_hash.hexdigest()
                  code_challenge = base64.urlsafe_b64encode(code_verifier_hash.digest())[:43]
                  
                  transient_config = {
                        "code_verifier": code_verifier,
                        "code_challenge": code_challenge,
                        "code_challenge_method": "S256",
                        "state": sha256(f"oauth_{service}_state_{now}".encode("utf8")).hexdigest(),
                  }
                  config["request_token_params"].update(transient_config)
                  session[transient_config_key] = transient_config
            else:
                  config["access_token_params"]["code_verifier"] = transient_config["code_verifier"]
                  config["access_token_params"]["client_id"] = config["consumer_key"]

            app = Flask(__name__)
            oauth = OAuth(app)
            remote_app = oauth.remote_app(service, **config)

            @remote_app.tokengetter
            def get_token(token=None):
                  return session[f"{service}_token"]
            
            return remote_app

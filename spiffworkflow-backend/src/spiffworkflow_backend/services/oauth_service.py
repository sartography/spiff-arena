
from spiffworkflow_backend.services.secret_service import SecretService

from typing import Dict, List, Any

from flask import Flask
from flask_oauthlib.client import OAuth

# TODO: get this from somewhere dynamic, admins need to edit from the UI
# TODO: ^ in the interim, need to get client_id/secret from env? secrets?
# TODO: also don't like the name
AUTHS = {
      "airtable": {
            "consumer_key": "SPIFF_SECRET:AIRTABLE_CONSUMER_KEY",
            "consumer_secret": "SPIFF_SECRET:AIRTABLE_CONSUMER_SECRET",
            "request_token_params": { "scope": "data.records:read schema.bases:read" },
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
                        value = SecretService.resolve_possibly_secret_value(config[k])
                        print(f"HERE: {k} -> {value}")
                        config[k] = value

            print(config)

            app = Flask(__name__)
            oauth = OAuth(app)
            remote_app = oauth.remote_app(service, **config)

            token_store = {}

            @remote_app.tokengetter
            def get_token(token=None):
                  return token_store.get('token')
            
            return remote_app

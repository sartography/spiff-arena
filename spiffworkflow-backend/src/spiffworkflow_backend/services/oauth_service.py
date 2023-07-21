from typing import Dict, List, Any

# TODO: get this from somewhere dynamic, admins need to edit from the UI
# TODO: ^ in the interim, need to get client_id/secret from env? secrets?
# TODO: also don't like the name
AUTHS = {
      "airtable": {
            "name": "airtable",
            "version": "2",
            "client_id": "XXX",
            "client_secret": "XXX",
            "endpoint_url": "https://airtable.com/",
            "authorization_url": "https://airtable.com/oauth2/v1/authorize",
            "access_token_url": "https://airtable.com/oauth2/v1/token",
            "refresh_token_url": "https://airtable.com/oauth2/v1/token",
            "scope": "data.records:read schema.bases:read",
      },
}

class OAuthService:
      @staticmethod
      def authentication_list() -> List[Dict[str, Any]]:
            # TODO: build from AUTHS
            return [{"id": "airtable/OAuth", "parameters": []}]

      @staticmethod
      def supported_service(service: str) -> bool:
            return service in AUTHS

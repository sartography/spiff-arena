"""Oauth."""


class OAuth:
    """OAuth."""

    def __init__(self, client_id: str, client_secret: str):
        """__init__."""
        self.client_id = client_id
        self.client_secret = client_secret

    def app_description(self):
        """App_description."""
        return {
            "name": "xero",
            "version": "2",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "endpoint_url": "https://api.xero.com/",
            "authorization_url": "https://login.xero.com/identity/connect/authorize",
            "access_token_url": "https://identity.xero.com/connect/token",
            "refresh_token_url": "https://identity.xero.com/connect/token",
            "scope": "offline_access openid profile email accounting.transactions "
            "accounting.reports.read accounting.journals.read accounting.settings "
            "accounting.contacts accounting.attachments assets projects",
        }

    @staticmethod
    def filtered_params(params):
        """Filtered_params."""
        return {
            "client_id": params["client_id"],
            "client_secret": params["client_secret"],
        }

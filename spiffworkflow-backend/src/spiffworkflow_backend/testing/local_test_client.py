from urllib.parse import urlparse

from flask import current_app
from werkzeug.test import Client


class LocalTestClient:
    """A wrapper around the werkzeug test client.

    This provides a convenient way to make api calls to the application
    in the current app context. This is useful for things like bootstrapping
    where we want to call our own api, but we don't have a running server.
    """

    def __init__(self, client: Client | None = None):
        if client:
            self.client = client
        else:
            self.client = current_app.test_client()

    def _get_path(self, url: str) -> str:
        return urlparse(url).path

    def get(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        return self.client.get(path, **kwargs)

    def post(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        return self.client.post(path, **kwargs)

    def put(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        return self.client.put(path, **kwargs)

    def patch(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        return self.client.patch(path, **kwargs)

    def delete(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        return self.client.delete(path, **kwargs)

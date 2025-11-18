from urllib.parse import urlparse

from flask import current_app
from werkzeug.test import Client


class LocalTestClient:
    """A wrapper around the connexion test client.

    This provides a convenient way to make api calls to the application
    in the current app context. This is useful for things like bootstrapping
    where we want to call our own api, but we don't have a running server.
    """

    def __init__(self, client: Client | None = None):
        if client:
            self.client = client
        else:
            # Try to use connexion app test client if available for proper API routing
            connexion_app = getattr(current_app, 'config', {}).get('CONNEXION_APP')
            if connexion_app and hasattr(connexion_app, 'test_client'):
                try:
                    self.client = connexion_app.test_client()
                except Exception:
                    # Fall back to Flask test client if connexion client creation fails
                    self.client = current_app.test_client()
            else:
                self.client = current_app.test_client()

    def _get_path(self, url: str) -> str:
        return urlparse(url).path

    def _convert_kwargs(self, **kwargs):
        """Convert Flask test client kwargs to work with connexion test client."""
        converted = {}

        # Handle query_string -> params conversion for connexion/httpx client
        if 'query_string' in kwargs:
            query_string = kwargs.pop('query_string')
            if query_string:
                converted['params'] = query_string

        # Handle headers - most test clients support this
        if 'headers' in kwargs and kwargs['headers'] is not None:
            converted['headers'] = kwargs['headers']

        # For GET requests, don't pass json data - use params or headers only
        # For other methods, we can try json but it might not be supported

        # Only pass through commonly supported kwargs
        supported_kwargs = ['headers', 'params']
        for key, value in kwargs.items():
            if key in supported_kwargs and value is not None:
                converted[key] = value

        return converted

    def get(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        converted_kwargs = self._convert_kwargs(**kwargs)
        return self.client.get(path, **converted_kwargs)

    def post(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        converted_kwargs = self._convert_kwargs(**kwargs)
        return self.client.post(path, **converted_kwargs)

    def put(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        converted_kwargs = self._convert_kwargs(**kwargs)
        return self.client.put(path, **converted_kwargs)

    def patch(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        converted_kwargs = self._convert_kwargs(**kwargs)
        return self.client.patch(path, **converted_kwargs)

    def delete(self, url: str, **kwargs) -> any:
        path = self._get_path(url)
        converted_kwargs = self._convert_kwargs(**kwargs)
        return self.client.delete(path, **converted_kwargs)

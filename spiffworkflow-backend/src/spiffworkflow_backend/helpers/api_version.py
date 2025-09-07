from urllib.parse import urlparse

from flask import current_app

V1_API_PATH_PREFIX = "/v1.0"


def remove_api_prefix(path: str) -> str:
    api_path_prefix = current_app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"]
    if path.startswith(api_path_prefix):
        return path.removeprefix(api_path_prefix)

    # permission check requests from frontend include /v1.0, but never include /api
    if path.startswith(V1_API_PATH_PREFIX):
        return path.removeprefix(V1_API_PATH_PREFIX)

    return path


def build_api_url(backend_url: str, api_path_prefix: str, endpoint: str) -> str:
    """Build a URL ensuring no duplicate API path segments.

    This function handles cases where the backend_url might end with a path segment
    that matches the beginning of the api_path_prefix (e.g., '/api') to prevent
    duplicate path segments in the resulting URL.

    Args:
        backend_url: Base URL for the backend (e.g., 'http://example.com/api')
        api_path_prefix: API path prefix (e.g., '/api/v1.0')
        endpoint: The specific endpoint to access (e.g., 'process-data-file-download/123')

    Returns:
        A properly constructed URL without duplicate path segments
    """
    parsed_url = urlparse(backend_url)
    backend_path = parsed_url.path

    # Check if backend URL ends with a segment that API path prefix starts with
    if backend_path.endswith("/api") and api_path_prefix.startswith("/api"):
        # Replace the ending /api with empty string to avoid duplication
        backend_path = backend_path[:-4]
        url = parsed_url._replace(path=backend_path).geturl() + api_path_prefix + "/" + endpoint
    else:
        url = backend_url + api_path_prefix + "/" + endpoint

    return url

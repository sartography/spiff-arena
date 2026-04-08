from spiffworkflow_backend.helpers.api_version import V1_API_PATH_PREFIX


def build_public_api_v1_url(backend_url: str, endpoint: str) -> str:
    """Build a public v1 API URL from the externally reachable backend base URL.

    The backend URL may already include a mount path such as ``/api``. Public API
    endpoints always live under ``/v1.0`` relative to that base URL.
    """

    base_url = backend_url.rstrip("/")
    endpoint_path = endpoint.lstrip("/")
    api_base_url = f"{base_url}{V1_API_PATH_PREFIX}"
    if endpoint_path == "":
        return api_base_url
    return f"{api_base_url}/{endpoint_path}"

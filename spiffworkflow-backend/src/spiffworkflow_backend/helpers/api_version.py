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

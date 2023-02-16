"""Default."""
from os import environ

environment_identifier_for_this_config_file_only = environ["SPIFFWORKFLOW_BACKEND_ENV"]
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL = (
    f"https://keycloak.{environment_identifier_for_this_config_file_only}"
    ".spiffworkflow.org/realms/sartography"
)
SPIFFWORKFLOW_BACKEND_GIT_BRANCH = environ.get(
    "SPIFFWORKFLOW_BACKEND_GIT_BRANCH", default="main"
)
SPIFFWORKFLOW_BACKEND_GIT_CLONE_URL_FOR_PUBLISHING = environ.get(
    "GIT_CLONE_URL",
    default="https://github.com/sartography/sartography-process-models.git",
)

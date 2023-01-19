"""Default."""
from os import environ

environment_identifier_for_this_config_file_only = environ["SPIFFWORKFLOW_BACKEND_ENV"]
OPEN_ID_SERVER_URL = f"https://keycloak.{environment_identifier_for_this_config_file_only}.spiffworkflow.org/realms/sartography"
GIT_BRANCH = environ.get("GIT_BRANCH", default="main")
GIT_CLONE_URL_FOR_PUBLISHING = environ.get(
    "GIT_CLONE_URL",
    default="https://github.com/sartography/sartography-process-models.git",
)

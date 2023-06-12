"""Terraform-deployed environment."""
from os import environ

# default.py already ensured that this key existed as was not None
environment_identifier_for_this_config_file_only = environ["SPIFFWORKFLOW_BACKEND_ENV"]

SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE = True
SPIFFWORKFLOW_BACKEND_GIT_USERNAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_GIT_USERNAME", default="sartography-automated-committer"
)
SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL = environ.get(
    "SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL",
    default=f"{SPIFFWORKFLOW_BACKEND_GIT_USERNAME}@users.noreply.github.com",
)
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME",
    default="terraform_deployed_environment.yml",
)

SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER = (
    environ.get("SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER", default="false") == "true"
)

SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL",
    default=(
        f"https://keycloak.{environment_identifier_for_this_config_file_only}.spiffworkflow.org/realms/spiffworkflow"
    ),
)

SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND = environ.get(
    "SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND",
    default=f"https://{environment_identifier_for_this_config_file_only}.spiffworkflow.org",
)
SPIFFWORKFLOW_BACKEND_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_URL",
    default=f"https://api.{environment_identifier_for_this_config_file_only}.spiffworkflow.org",
)
SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL",
    default=f"https://connector-proxy.{environment_identifier_for_this_config_file_only}.spiffworkflow.org",
)
SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL",
    default="https://github.com/sartography/sample-process-models.git",
)

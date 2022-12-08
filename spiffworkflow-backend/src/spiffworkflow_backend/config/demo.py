"""Demo environment."""
from os import environ

GIT_COMMIT_ON_SAVE = True
GIT_USERNAME = "demo"
GIT_USER_EMAIL = "demo@example.com"
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME",
    default="terraform_deployed_environment.yml",
)

RUN_BACKGROUND_SCHEDULER = (
    environ.get("RUN_BACKGROUND_SCHEDULER", default="false") == "true"
)

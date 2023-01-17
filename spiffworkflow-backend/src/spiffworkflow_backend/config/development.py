"""Development."""
from os import environ

SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME", default="development.yml"
)

SPIFFWORKFLOW_BACKEND_LOG_LEVEL = environ.get(
    "SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="debug"
)

RUN_BACKGROUND_SCHEDULER = (
    environ.get("RUN_BACKGROUND_SCHEDULER", default="false") == "true"
)
GIT_CLONE_URL_FOR_PUBLISHING = environ.get(
    "GIT_CLONE_URL", default="https://github.com/sartography/sample-process-models.git"
)
GIT_USERNAME = "sartography-automated-committer"
GIT_USER_EMAIL = f"{GIT_USERNAME}@users.noreply.github.com"

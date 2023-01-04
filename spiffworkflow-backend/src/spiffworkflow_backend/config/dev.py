"""Dev."""
from os import environ

GIT_BRANCH_TO_PUBLISH_TO = environ.get("GIT_BRANCH_TO_PUBLISH_TO", default="staging")
GIT_USERNAME = environ.get("GIT_USERNAME", default="sartography-automated-committer")
GIT_USER_EMAIL = environ.get(
    "GIT_USER_EMAIL", default="sartography-automated-committer@users.noreply.github.com"
)
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = "dev.yml"

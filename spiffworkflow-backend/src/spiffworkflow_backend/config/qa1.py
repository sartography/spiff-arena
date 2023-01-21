"""Qa1."""
from os import environ

GIT_BRANCH_TO_PUBLISH_TO = environ.get("GIT_BRANCH_TO_PUBLISH_TO", default="qa2")
GIT_USERNAME = environ.get("GIT_USERNAME", default="sartography-automated-committer")
GIT_USER_EMAIL = environ.get(
    "GIT_USER_EMAIL", default=f"{GIT_USERNAME}@users.noreply.github.com"
)
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME", default="qa1.yml"
)

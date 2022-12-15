"""Staging."""
from os import environ

GIT_BRANCH = environ.get("GIT_BRANCH_TO_PUBLISH_TO", default="staging")
GIT_BRANCH_TO_PUBLISH_TO = environ.get("GIT_BRANCH_TO_PUBLISH_TO", default="main")
GIT_COMMIT_ON_SAVE = False
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = "staging.yml"

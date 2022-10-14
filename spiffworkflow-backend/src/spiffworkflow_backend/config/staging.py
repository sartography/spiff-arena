"""Staging."""
from os import environ

GIT_COMMIT_ON_SAVE = True
GIT_COMMIT_USERNAME = "staging"
GIT_COMMIT_EMAIL = "staging@example.com"
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME", default="staging.yml"
)

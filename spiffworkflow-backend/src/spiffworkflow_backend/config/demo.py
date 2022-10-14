"""Staging."""
from os import environ

GIT_COMMIT_ON_SAVE = True
GIT_COMMIT_USERNAME = "demo"
GIT_COMMIT_EMAIL = "demo@example.com"
SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME", default="demo.yml"
)

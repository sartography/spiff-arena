"""Testing.py."""
from os import environ


TESTING = True
SECRET_KEY = "the_secret_key"
SPIFFWORKFLOW_BACKEND_LOG_TO_FILE = (
    environ.get("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default="true") == "true"
)

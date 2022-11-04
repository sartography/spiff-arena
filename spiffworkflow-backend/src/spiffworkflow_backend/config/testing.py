"""Testing.py."""
import os
from os import environ

TESTING = True
SECRET_KEY = "the_secret_key"
SPIFFWORKFLOW_BACKEND_LOG_TO_FILE = (
    environ.get("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default="true") == "true"
)

SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME", default="testing.yml"
)

SPIFFWORKFLOW_BACKEND_LOG_LEVEL = environ.get(
    "SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="debug"
)

# NOTE: set this here since nox shoves tests and src code to
# different places and this allows us to know exactly where we are at the start
BPMN_SPEC_ABSOLUTE_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "tests",
    "spiffworkflow_backend",
    "files",
    "bpmn_specs",
)

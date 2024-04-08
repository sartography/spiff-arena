"""Testing.py."""

import os
from os import environ

TESTING = True
SPIFFWORKFLOW_BACKEND_LOG_TO_FILE = environ.get("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default="true") == "true"

SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = "unit_testing.yml"

SPIFFWORKFLOW_BACKEND_URL = "http://localhost"
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL = "http://localhost/openid"
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID = "spiffworkflow-backend"
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY = "JXeQExm0JhQPLumgHtIIqf52bDalHz0q"  # noqa: S105
SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS = None

SPIFFWORKFLOW_BACKEND_LOG_LEVEL = environ.get("SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="debug")
SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE = False

SPIFFWORKFLOW_BACKEND_WEBHOOK_PROCESS_MODEL_IDENTIFIER = "test_group/simple_script"
SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET = "test_github_webhook_secret"  # noqa: S105

# NOTE: set this here since nox shoves tests and src code to
# different places and this allows us to know exactly where we are at the start
worker_id = environ.get("PYTEST_XDIST_WORKER")
parallel_test_suffix = ""
if worker_id is not None:
    parallel_test_suffix = f"_{worker_id}"
SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "..",
    "..",
    "tests",
    "spiffworkflow_backend",
    "files",
    f"bpmn_specs{parallel_test_suffix}",
)

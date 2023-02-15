"""Default."""
import re
from os import environ

BPMN_SPEC_ABSOLUTE_DIR = environ.get("BPMN_SPEC_ABSOLUTE_DIR")
cors_allow_all = "*"
CORS_ALLOW_ORIGINS = re.split(
    r",\s*", environ.get("CORS_ALLOW_ORIGINS", default=cors_allow_all)
)

RUN_BACKGROUND_SCHEDULER = (
    environ.get("RUN_BACKGROUND_SCHEDULER", default="false") == "true"
)
SPIFFWORKFLOW_FRONTEND_URL = environ.get(
    "SPIFFWORKFLOW_FRONTEND_URL", default="http://localhost:7001"
)
SPIFFWORKFLOW_BACKEND_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_URL", default="http://localhost:7000"
)
# service task connector proxy
CONNECTOR_PROXY_URL = environ.get(
    "CONNECTOR_PROXY_URL", default="http://localhost:7004"
)

# Open ID server
OPEN_ID_SERVER_URL = environ.get(
    "OPEN_ID_SERVER_URL",
    default="http://localhost:7002/realms/spiffworkflow"
    # "OPEN_ID_SERVER_URL", default="http://localhost:7000/openid"
)

# Replace above line with this to use the built-in Open ID Server.
# OPEN_ID_SERVER_URL = environ.get("OPEN_ID_SERVER_URL", default="http://localhost:7000/openid")
OPEN_ID_CLIENT_ID = environ.get("OPEN_ID_CLIENT_ID", default="spiffworkflow-backend")
OPEN_ID_CLIENT_SECRET_KEY = environ.get(
    "OPEN_ID_CLIENT_SECRET_KEY", default="JXeQExm0JhQPLumgHtIIqf52bDalHz0q"
)  # noqa: S105

# Tenant specific fields is a comma separated list of field names that we will convert to list of strings
# and store in the user table's tenant_specific_field_n columns. You can have up to three items in this
# comma-separated list.
OPEN_ID_TENANT_SPECIFIC_FIELDS = environ.get("OPEN_ID_TENANT_SPECIFIC_FIELDS")

SPIFFWORKFLOW_BACKEND_LOG_TO_FILE = (
    environ.get("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default="false") == "true"
)

SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"
)

# Sentry Configuration
SENTRY_DSN = environ.get("SENTRY_DSN", default="")
SENTRY_ERRORS_SAMPLE_RATE = environ.get(
    "SENTRY_ERRORS_SAMPLE_RATE", default="1"
)  # send all errors
SENTRY_TRACES_SAMPLE_RATE = environ.get(
    "SENTRY_TRACES_SAMPLE_RATE", default="0.01"
)  # send 1% of traces

SPIFFWORKFLOW_BACKEND_LOG_LEVEL = environ.get(
    "SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="info"
)

# When a user clicks on the `Publish` button, this is the default branch this server merges into.
# I.e., dev server could have `staging` here. Staging server might have `production` here.
GIT_BRANCH_TO_PUBLISH_TO = environ.get("GIT_BRANCH_TO_PUBLISH_TO")
GIT_BRANCH = environ.get("GIT_BRANCH")
GIT_CLONE_URL_FOR_PUBLISHING = environ.get("GIT_CLONE_URL")
GIT_COMMIT_ON_SAVE = environ.get("GIT_COMMIT_ON_SAVE", default="false") == "true"
GIT_SSH_PRIVATE_KEY = environ.get("GIT_SSH_PRIVATE_KEY")
GIT_USERNAME = environ.get("GIT_USERNAME")
GIT_USER_EMAIL = environ.get("GIT_USER_EMAIL")

# Database Configuration
SPIFF_DATABASE_TYPE = environ.get(
    "SPIFF_DATABASE_TYPE", default="mysql"
)  # can also be sqlite, postgres
# Overide above with specific sqlalchymy connection string.
SPIFFWORKFLOW_BACKEND_DATABASE_URI = environ.get(
    "SPIFFWORKFLOW_BACKEND_DATABASE_URI", default=None
)
SYSTEM_NOTIFICATION_PROCESS_MODEL_MESSAGE_ID = environ.get(
    "SYSTEM_NOTIFICATION_PROCESS_MODEL_MESSAGE_ID",
    default="Message_SystemMessageNotification",
)

ALLOW_CONFISCATING_LOCK_AFTER_SECONDS = int(
    environ.get("ALLOW_CONFISCATING_LOCK_AFTER_SECONDS", default="600")
)

SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP = environ.get(
    "SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP", default="everybody"
)

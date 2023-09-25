import re
from os import environ

# Consider: https://flask.palletsprojects.com/en/2.2.x/config/#configuring-from-environment-variables
#   and from_prefixed_env(), though we want to ensure that these variables are all documented, so that
#   is a benefit of the status quo and having them all in this file explicitly.


def config_from_env(variable_name: str, *, default: str | bool | int | None = None) -> None:
    value_from_env: str | None = environ.get(variable_name)
    if value_from_env == "":
        value_from_env = None
    value_to_return: str | bool | int | None = value_from_env
    if value_from_env is not None:
        if isinstance(default, bool):
            if value_from_env.lower() == "true":
                value_to_return = True
            if value_from_env.lower() == "false":
                value_to_return = False
        elif isinstance(default, int):
            value_to_return = int(value_from_env)
    if value_to_return is None:
        value_to_return = default
    globals()[variable_name] = value_to_return


config_from_env("FLASK_SESSION_SECRET_KEY")

config_from_env("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR")
config_from_env("SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX", default="extensions")
config_from_env("SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED", default=False)

cors_allow_all = "*"
SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS = re.split(
    r",\s*",
    environ.get("SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS", default=cors_allow_all),
)

config_from_env("SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER_IN_CREATE_APP", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_ALLOW_OPTIMISTIC_CHECKS", default=True)

config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_POLLING_INTERVAL_IN_SECONDS", default=10)
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_NOT_STARTED_POLLING_INTERVAL_IN_SECONDS", default=30)
config_from_env(
    "SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_USER_INPUT_REQUIRED_POLLING_INTERVAL_IN_SECONDS", default=120
)

# we only use this in one place, and it checks to see if it is None.
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_POOL_SIZE")

config_from_env("SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND", default="http://localhost:7001")
config_from_env("SPIFFWORKFLOW_BACKEND_URL", default="http://localhost:7000")
config_from_env("SPIFFWORKFLOW_BACKEND_CHECK_FRONTEND_AND_BACKEND_URL_COMPATIBILITY", default=True)
# service task connector proxy
config_from_env("SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL", default="http://localhost:7004")
config_from_env(
    "SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPEAHEAD_URL",
    default="https://emehvlxpwodjawtgi7ctkbvpse0vmaow.lambda-url.us-east-1.on.aws",
)

# Open ID server
# use "http://localhost:7000/openid" for running with simple openid
# server hosted by spiffworkflow-backend
config_from_env(
    "SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL",
    default="http://localhost:7002/realms/spiffworkflow",
)

config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID", default="spiffworkflow-backend")
config_from_env(
    "SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY",
    default="JXeQExm0JhQPLumgHtIIqf52bDalHz0q",
)  # noqa: S105

# Tenant specific fields is a comma separated list of field names that we will be converted to list of strings
# and store in the user table's tenant_specific_field_n columns. You can have up to three items in this
# comma-separated list.
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS")

config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_AUTHENTICATION_DISABLED", default=False)

# loggers to use is a comma separated list of logger prefixes that we will be converted to list of strings
config_from_env("SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE")

# cryptography or simple-crypt
config_from_env(
    # "SPIFFWORKFLOW_BACKEND_ENCRYPTION_LIB", default="cryptography"
    "SPIFFWORKFLOW_BACKEND_ENCRYPTION_LIB",
    default="no_op_cipher",
)

config_from_env("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default=False)

config_from_env("SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH")
config_from_env("SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME")

# Sentry Configuration
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_DSN", default="")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE", default="1")  # send all errors
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE", default="0.01")  # send 1% of traces
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_ORGANIZATION_SLUG")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_PROJECT_SLUG")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_ENV_IDENTIFIER")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_PROFILING_ENABLED", default=False)

config_from_env("SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="info")

# When a user clicks on the `Publish` button, this is the default branch this server merges into.
# I.e., dev server could have `staging` here. Staging server might have `production` here.
config_from_env("SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_TARGET_BRANCH")
# This is the branch that the app automatically commits to every time the user clicks the save button
# or otherwise changes a process model.
# If publishing is enabled, the contents of this "staging area" / "scratch pad" / WIP spot will be used
# as the relevant contents for process model that the user wants to publish.
config_from_env("SPIFFWORKFLOW_BACKEND_GIT_SOURCE_BRANCH")
config_from_env("SPIFFWORKFLOW_BACKEND_GIT_PUBLISH_CLONE_URL")
config_from_env("SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_GIT_USERNAME")
config_from_env("SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL")
config_from_env("SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET")
config_from_env("SPIFFWORKFLOW_BACKEND_GIT_SSH_PRIVATE_KEY_PATH")

# Database Configuration
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE", default="mysql")  # can also be sqlite, postgres
# Overide above with specific sqlalchymy connection string.
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_URI")
config_from_env(
    "SPIFFWORKFLOW_BACKEND_SYSTEM_NOTIFICATION_PROCESS_MODEL_MESSAGE_ID",
    default="Message_SystemMessageNotification",
)

config_from_env("SPIFFWORKFLOW_BACKEND_ALLOW_CONFISCATING_LOCK_AFTER_SECONDS", default="600")

# FIXME: do not default this but we will need to coordinate release of it since it is a breaking change
config_from_env("SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP", default="everybody")

config_from_env("SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND", default="greedy")

config_from_env("SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_WEB", default="run_until_user_message")

# this is only used in CI. use SPIFFWORKFLOW_BACKEND_DATABASE_URI instead for real configuration
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_PASSWORD")

# we load the CustomBpmnScriptEngine at import time, where we do not have access to current_app,
# so instead of using config, we use os.environ directly over there.
# config_from_env("SPIFFWORKFLOW_BACKEND_USE_RESTRICTED_SCRIPT_ENGINE", default=True)

config_from_env("SPIFFWORKFLOW_BACKEND_FEATURE_ELEMENT_UNITS_ENABLED", default=False)

config_from_env("SPIFFWORKFLOW_BACKEND_ELEMENT_UNITS_CACHE_DIR", default="src/instance/element-unit-cache")

# adds the ProxyFix to Flask on http by processing the 'X-Forwarded-Proto' header
# to make SpiffWorkflow aware that it should return https for the server urls etc rather than http.
config_from_env("SPIFFWORKFLOW_BACKEND_USE_WERKZEUG_MIDDLEWARE_PROXY_FIX", default=False)

config_from_env("SPIFFWORKFLOW_BACKEND_MAX_INSTANCE_LOCK_DURATION_IN_SECONDS", default="300")

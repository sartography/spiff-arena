import re
from os import environ
from typing import Any

from spiffworkflow_backend.config.normalized_environment import normalized_environment

# Consider: https://flask.palletsprojects.com/en/2.2.x/config/#configuring-from-environment-variables
#   and from_prefixed_env(), though we want to ensure that these variables are all documented, so that
#   is a benefit of the status quo and having them all in this file explicitly.


def config_from_env(variable_name: str, *, default: str | bool | int | None = None) -> Any:
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

    # NOTE: using this method in other config python files will NOT overwrite
    # the value set in the variable here. It is better to set the variables like
    # normal in them so they can take effect.
    globals()[variable_name] = value_to_return
    return value_to_return


configs_with_structures = normalized_environment(environ)

### basic
config_from_env("FLASK_SESSION_SECRET_KEY")
config_from_env("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR")

### extensions
config_from_env("SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX", default="extensions")
config_from_env("SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED", default=False)

### background processor
config_from_env("SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER_IN_CREATE_APP", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_ALLOW_OPTIMISTIC_CHECKS", default=True)
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_POLLING_INTERVAL_IN_SECONDS", default=10)
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_NOT_STARTED_POLLING_INTERVAL_IN_SECONDS", default=30)
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_USER_INPUT_REQUIRED_POLLING_INTERVAL_IN_SECONDS", default=120)

### background with celery
config_from_env("SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_CELERY_BROKER_URL", default="redis://localhost")
config_from_env("SPIFFWORKFLOW_BACKEND_CELERY_RESULT_BACKEND", default="redis://localhost")

# give a little overlap to ensure we do not miss items although the query will handle it either way
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_FUTURE_TASK_LOOKAHEAD_IN_SECONDS", default=301)
config_from_env("SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_FUTURE_TASK_EXECUTION_INTERVAL_IN_SECONDS", default=300)

### frontend
config_from_env("SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND", default="http://localhost:7001")
config_from_env("SPIFFWORKFLOW_BACKEND_URL", default="http://localhost:7000")
config_from_env("SPIFFWORKFLOW_BACKEND_CHECK_FRONTEND_AND_BACKEND_URL_COMPATIBILITY", default=True)
cors_allow_all = "*"
SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS = re.split(
    r",\s*",
    environ.get("SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS", default=cors_allow_all),
)

### service task connector proxy
config_from_env("SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL", default="http://localhost:7004")
config_from_env(
    "SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPEAHEAD_URL",
    default="https://emehvlxpwodjawtgi7ctkbvpse0vmaow.lambda-url.us-east-1.on.aws",
)

### database
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE", default="mysql")  # can also be sqlite, postgres
# Overide above with specific sqlalchymy connection string.
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_URI")
# NOTE: this is only used in CI. use SPIFFWORKFLOW_BACKEND_DATABASE_URI instead for real configuration
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_PASSWORD")
# we only use this in one place, and it checks to see if it is None.
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_POOL_SIZE")

### open id
config_from_env("SPIFFWORKFLOW_BACKEND_AUTHENTICATION_DISABLED", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", default=False)
# Tenant specific fields is a comma separated list of field names that we will be converted to list of strings
# and store in the user table's tenant_specific_field_n columns. You can have up to three items in this
# comma-separated list.
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS")

# Open ID server
# use "http://localhost:7000/openid" for running with simple openid
# server hosted by spiffworkflow-backend
if "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS" in configs_with_structures:
    SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS = configs_with_structures["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"]
else:
    # do this for now for backwards compatibility
    url_config = config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL")
    if url_config is not None:
        SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL = url_config
        config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID", default="spiffworkflow-backend")
        config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY", default="JXeQExm0JhQPLumgHtIIqf52bDalHz0q")

        # comma-separated list of client ids that can be successfully validated against.
        # useful for api users that will login to a different client on the same realm but from something external to backend.
        # Example:
        #       client-A is configured as the main client id in backend
        #       client-B is for api users who will authenticate directly with keycloak
        #       if client-B is added to this list, then an api user can auth with keycloak
        #           and use that token successfully with backend
        config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_ADDITIONAL_VALID_CLIENT_IDS")
    else:
        SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS = [
            {
                "identifier": "default",
                "label": "Default",
                "uri": "http://localhost:7002/realms/spiffworkflow",
                "client_id": "spiffworkflow-backend",
                "client_secret": "JXeQExm0JhQPLumgHtIIqf52bDalHz0q",
                "additional_valid_client_ids": None,
            }
        ]

### logs
# loggers to use is a comma separated list of logger prefixes that we will be converted to list of strings
config_from_env("SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE")
config_from_env("SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="info")
config_from_env("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default=False)

### permissions
config_from_env("SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH")
config_from_env("SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME")
# FIXME: do not default this but we will need to coordinate release of it since it is a breaking change
config_from_env("SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP", default="everybody")

### sentry
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_DSN", default="")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE", default="1")  # send all errors
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE", default="0.01")  # send 1% of traces
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_ORGANIZATION_SLUG")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_PROJECT_SLUG")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_ENV_IDENTIFIER")
config_from_env("SPIFFWORKFLOW_BACKEND_SENTRY_PROFILING_ENABLED", default=False)

### git and publish
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

### element units
# disabling until we fix the "no such directory" error so we do not keep sending cypress errors
config_from_env("SPIFFWORKFLOW_BACKEND_ELEMENT_UNITS_CACHE_DIR", default="src/instance/element-unit-cache")

### cryptography (to encrypt) or no_op_cipher (to not encrypt)
config_from_env(
    # "SPIFFWORKFLOW_BACKEND_ENCRYPTION_LIB", default="cryptography"
    "SPIFFWORKFLOW_BACKEND_ENCRYPTION_LIB",
    default="no_op_cipher",
)
config_from_env("SPIFFWORKFLOW_BACKEND_ENCRYPTION_KEY")

### locking
# timeouts for process instances locks as they are run to avoid stale locks
config_from_env("SPIFFWORKFLOW_BACKEND_ALLOW_CONFISCATING_LOCK_AFTER_SECONDS", default="600")
config_from_env("SPIFFWORKFLOW_BACKEND_MAX_INSTANCE_LOCK_DURATION_IN_SECONDS", default="300")

### other
config_from_env(
    "SPIFFWORKFLOW_BACKEND_SYSTEM_NOTIFICATION_PROCESS_MODEL_MESSAGE_ID",
    default="Message_SystemMessageNotification",
)
# check all tasks listed as child tasks are saved to the database
config_from_env("SPIFFWORKFLOW_BACKEND_DEBUG_TASK_CONSISTENCY", default=False)

### for documentation only
# we load the CustomBpmnScriptEngine at import time, where we do not have access to current_app,
# so instead of using config, we use os.environ directly over there.
# config_from_env("SPIFFWORKFLOW_BACKEND_USE_RESTRICTED_SCRIPT_ENGINE", default=True)
# adds the ProxyFix to Flask on http by processing the 'X-Forwarded-Proto' header
# to make SpiffWorkflow aware that it should return https for the server urls etc rather than http.
config_from_env("SPIFFWORKFLOW_BACKEND_USE_WERKZEUG_MIDDLEWARE_PROXY_FIX", default=False)

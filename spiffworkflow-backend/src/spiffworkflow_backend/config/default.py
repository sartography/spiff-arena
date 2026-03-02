import re
from os import environ
from typing import Any

from flask import current_app

from spiffworkflow_backend.config.normalized_environment import normalized_environment

# Consider: https://flask.palletsprojects.com/en/2.2.x/config/#configuring-from-environment-variables
#   and from_prefixed_env(), though we want to ensure that these variables are all documented, so that
#   is a benefit of the status quo and having them all in this file explicitly.


def config_from_env(variable_name: str, *, default: str | bool | int | None = None) -> Any:
    value_from_env: str | None = environ.get(variable_name)
    if value_from_env == "":
        value_from_env = None

    value_to_return: str | bool | int | None = value_from_env
    # using docker secrets - put file contents to env value
    if variable_name.endswith("_FILE"):
        value_from_file = default if value_from_env is None else value_from_env
        if value_from_file:
            if isinstance(value_from_file, str) and value_from_file.startswith("/run/secrets"):
                # rewrite variable name: remove _FILE
                variable_name = variable_name.removesuffix("_FILE")
                try:
                    with open(value_from_file) as file:
                        value_to_return = file.read().strip()  # Read entire content and strip any extra whitespace
                except FileNotFoundError:
                    value_to_return = None  # Handle the case where the file does not exist
                except Exception as e:
                    current_app.logger.error(f"Error reading from {value_from_file}: {str(e)}")
                    value_to_return = None  # Handle other potential errors

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

### AI Tools
config_from_env("SPIFFWORKFLOW_BACKEND_SCRIPT_ASSIST_ENABLED", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_SECRET_KEY_OPENAI_API")

### extensions
config_from_env("SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX", default="extensions")
config_from_env("SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR", default=None)
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
config_from_env("SPIFFWORKFLOW_BACKEND_CELERY_RESULT_BACKEND", default=None)
config_from_env("SPIFFWORKFLOW_BACKEND_CELERY_SQS_URL", default=None)
config_from_env("SPIFFWORKFLOW_BACKEND_CELERY_RESULT_S3_BUCKET", default=None)
config_from_env("SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED", default=False)

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
config_from_env("SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_API_KEY", default=None)
config_from_env(
    "SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPEAHEAD_URL",
    default="https://emehvlxpwodjawtgi7ctkbvpse0vmaow.lambda-url.us-east-1.on.aws",
)

### model marketplace
config_from_env("SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL", default="https://model-marketplace.spiff.works")

### database
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE", default="mysql")  # can also be sqlite, postgres
# Overide above with specific sqlalchymy connection string.
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_URI")
# NOTE: this is only used in CI. use SPIFFWORKFLOW_BACKEND_DATABASE_URI instead for real configuration
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_PASSWORD")
# we only use this in one place, and it checks to see if it is None.
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_POOL_SIZE")
# check sqlalchemy's doc for more info about pool_pre_ping:
# https://docs.sqlalchemy.org/en/20/core/pooling.html#disconnect-handling-pessimistic
config_from_env("SPIFFWORKFLOW_BACKEND_DATABASE_POOL_PRE_PING", default=True)

### open id
config_from_env("SPIFFWORKFLOW_BACKEND_AUTHENTICATION_DISABLED", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_IS_AUTHORITY_FOR_USER_GROUPS", default=False)
# Tenant specific fields is a comma separated list of field names that we will be converted to list of strings
# and store in the user table's tenant_specific_field_n columns. You can have up to three items in this
# comma-separated list.
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS")
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_IAT", default=True)
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_NBF", default=True)
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_AZP", default=True)
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_LEEWAY", default=5)
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_INTERNAL_URL_IS_VALID_ISSUER", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_SCOPES", default="openid,profile,email")
config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_ENFORCE_PKCE", default=False)  # Set to enforce OAuth PKCE (recommended)

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
        config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_INTERNAL_URL")

        # comma-separated list of issuer URLs to validate against
        # This is useful for Azure Entra which has a server URL of
        # https://login.microsoftonline.com/<tenant-id>/v2.0 but the iss url is https://sts.windows.net/<tenant-id>/
        config_from_env("SPIFFWORKFLOW_BACKEND_OPEN_ID_ADDITIONAL_VALID_ISSUERS")

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
                "internal_uri": "http://localhost:7002/realms/spiffworkflow-local",
                "uri": "http://localhost:7002/realms/spiffworkflow-local",
                "client_id": "spiffworkflow-backend",
                "client_secret": "JXeQExm0JhQPLumgHtIIqf52bDalHz0q",
                "additional_valid_client_ids": None,
                "additional_valid_issuers": [],
            }
        ]


### logs
# loggers to use is a comma separated list of logger prefixes that we will be converted to list of strings
config_from_env("SPIFFWORKFLOW_BACKEND_LOGGERS_TO_USE")
config_from_env("SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="info")
config_from_env("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_LOG_LOGIN_LOGOUT", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_LOG_MILESTONES", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_EVENT_STREAM_HOST", default=None)
config_from_env("SPIFFWORKFLOW_BACKEND_EVENT_STREAM_PORT", default=None)
config_from_env("SPIFFWORKFLOW_BACKEND_EVENT_STREAM_SOURCE", default="spiffworkflow.org")
config_from_env("SPIFFWORKFLOW_BACKEND_API_LOGGING_ENABLED", default=False)
config_from_env("SPIFFWORKFLOW_BACKEND_API_LOG_ALL_ENDPOINTS", default=False)

### permissions
config_from_env("SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH")
config_from_env("SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME")
# FIXME: do not default this but we will need to coordinate release of it since it is a breaking change
config_from_env("SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP", default="everybody")
config_from_env("SPIFFWORKFLOW_BACKEND_DEFAULT_PUBLIC_USER_GROUP", default="spiff_public")

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
# If the BPMN spec dir is a subdir within a git repo, rather than the entire git repo, this is the path to that subdir
config_from_env("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_SUBDIR_WITHIN_REPO")

### webhook
# configs for handling incoming webhooks from other systems
# it assumes github webhooks by default, since SPIFFWORKFLOW_BACKEND_WEBHOOK_ENFORCES_GITHUB_AUTH is true,
# but if you set that to false, you can handle webhooks from any system. just make sure you supply your
# own auth checks in the process model.
# the github auth will use SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET from above.
config_from_env("SPIFFWORKFLOW_BACKEND_WEBHOOK_ENFORCES_GITHUB_AUTH", default=True)
config_from_env("SPIFFWORKFLOW_BACKEND_WEBHOOK_PROCESS_MODEL_IDENTIFIER")

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


### process instance file data
# if set then it will save files associated with process instances to this location
config_from_env("SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH")

### locking
# timeouts for process instances locks as they are run to avoid stale locks
config_from_env("SPIFFWORKFLOW_BACKEND_ALLOW_CONFISCATING_LOCK_AFTER_SECONDS", default="600")
config_from_env("SPIFFWORKFLOW_BACKEND_MAX_INSTANCE_LOCK_DURATION_IN_SECONDS", default="300")

### other
config_from_env(
    "SPIFFWORKFLOW_BACKEND_SYSTEM_NOTIFICATION_MESSAGE_NAME",
    default="SystemErrorMessage",
)
# process model to run when a process instance has been updated.
# currently only supported when running with celery.
config_from_env("SPIFFWORKFLOW_BACKEND_EVENT_NOTIFIER_PROCESS_MODEL")
# check all tasks listed as child tasks are saved to the database
config_from_env("SPIFFWORKFLOW_BACKEND_DEBUG_TASK_CONSISTENCY", default=False)

# When set to False, this will use the initiator for all task assignments.
# This is useful when using arena with api keys only and doing task assignment in a differnt system.
config_from_env("SPIFFWORKFLOW_BACKEND_USE_LANES_FOR_TASK_ASSIGNMENT", default=True)

### for documentation only
# we load the CustomBpmnScriptEngine at import time, where we do not have access to current_app,
# so instead of using config, we use os.environ directly over there.
# config_from_env("SPIFFWORKFLOW_BACKEND_USE_RESTRICTED_SCRIPT_ENGINE", default=True)
# config_from_env("SPIFFWORKFLOW_BACKEND_USE_NON_TASK_DATA_BASED_SCRIPT_ENGINE_ENVIRONMENT", default=False)

# adds the ProxyFix to Flask on http by processing the 'X-Forwarded-Proto' header
# to make SpiffWorkflow aware that it should return https for the server urls etc rather than http.
config_from_env("SPIFFWORKFLOW_BACKEND_USE_WERKZEUG_MIDDLEWARE_PROXY_FIX", default=False)

# how many proxies are in front of this flask server (for use with ProxyFix)
config_from_env("SPIFFWORKFLOW_BACKEND_PROXY_COUNT_FOR_PROXY_FIX", default=0)
config_from_env("SPIFFWORKFLOW_BACKEND_WSGI_PATH_PREFIX")

# only for DEBUGGING - turn off threaded task execution.
config_from_env("SPIFFWORKFLOW_BACKEND_USE_THREADS_FOR_TASK_EXECUTION", default=True)

config_from_env("SPIFFWORKFLOW_BACKEND_OPENID_SCOPE", default="openid profile email")

config_from_env("SPIFFWORKFLOW_BACKEND_USE_AUTH_FOR_METRICS", default=False)

### task validation
config_from_env("SPIFFWORKFLOW_BACKEND_VALIDATE_USER_TASK_DATA_AGAINST_SCHEMA", default=False)

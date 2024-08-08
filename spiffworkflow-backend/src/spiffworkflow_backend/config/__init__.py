"""__init__.py."""

import base64
import logging
import os
import threading
import uuid
from urllib.parse import urlparse

from flask.app import Flask
from werkzeug.utils import ImportStringError

from spiffworkflow_backend.services.logging_service import setup_logger_for_app

HTTP_REQUEST_TIMEOUT_SECONDS = 15
CONNECTOR_PROXY_COMMAND_TIMEOUT = 45
SUPPORTED_ENCRYPTION_LIBS = ["cryptography", "no_op_cipher"]


class ConfigurationError(Exception):
    pass


class NoOpCipher:
    def encrypt(self, value: str) -> bytes:
        return str.encode(value)

    def decrypt(self, value: str) -> str:
        return value


def setup_database_configs(app: Flask) -> None:
    worker_id = os.environ.get("PYTEST_XDIST_WORKER")
    parallel_test_suffix = ""
    if worker_id is not None:
        parallel_test_suffix = f"_{worker_id}"

    if app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_URI") is None:
        database_name = f"spiffworkflow_backend_{app.config['ENV_IDENTIFIER']}"
        if app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE") == "sqlite":
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{app.instance_path}/db_{app.config['ENV_IDENTIFIER']}{parallel_test_suffix}.sqlite3"
            )
        elif app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE") == "postgres":
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"postgresql://spiffworkflow_backend:spiffworkflow_backend@localhost:5432/{database_name}"
            )
        else:
            # use pswd to trick flake8 with hardcoded passwords
            db_pswd = app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_PASSWORD")
            if db_pswd is None:
                db_pswd = ""
            app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqldb://root:{db_pswd}@127.0.0.1/{database_name}"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_URI")

    # if pool size came in from the environment, it's a string, but we need an int
    # if it didn't come in from the environment, base it on the number of threads
    # note that max_overflow defaults to 10, so that will give extra buffer.
    pool_size = app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_POOL_SIZE")
    if pool_size is not None:
        pool_size = int(pool_size)
    else:
        # this one doesn't come from app config and isn't documented in default.py
        # because we don't want to give people the impression
        # that setting it in flask python configs will work. on the contrary, it's used by a bash
        # script that starts the backend, so it can only be set in the environment.
        threads_per_worker_config = os.environ.get("SPIFFWORKFLOW_BACKEND_THREADS_PER_WORKER")
        if threads_per_worker_config is not None:
            pool_size = int(threads_per_worker_config)
        else:
            # this is a sqlalchemy default, if we don't have any better ideas
            pool_size = 5

    pool_pre_ping = app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_POOL_PRE_PING")

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_size"] = pool_size
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_pre_ping"] = pool_pre_ping


def load_config_file(app: Flask, env_config_module: str) -> None:
    try:
        app.config.from_object(env_config_module)
    except ImportStringError:
        # ignore this error
        pass


def _set_up_tenant_specific_fields_as_list_of_strings(app: Flask) -> None:
    tenant_specific_fields = app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS")

    if tenant_specific_fields is None or tenant_specific_fields == "":
        app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS"] = []
    else:
        app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS"] = tenant_specific_fields.split(",")
        if len(app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS"]) > 3:
            raise ConfigurationError("SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS can have a maximum of 3 fields")


def _check_extension_api_configs(app: Flask) -> None:
    if (
        app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED"]
        and len(app.config["SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX"]) < 1
    ):
        raise ConfigurationError(
            "SPIFFWORKFLOW_BACKEND_EXTENSIONS_API_ENABLED is set to true but"
            " SPIFFWORKFLOW_BACKEND_EXTENSIONS_PROCESS_MODEL_PREFIX is an empty value."
        )


# see the message in the ConfigurationError below for why we are checking this.
# we really do not want this to raise when there is not a problem, so there are lots of return statements littered throughout.
def _check_for_incompatible_frontend_and_backend_urls(app: Flask) -> None:
    if not app.config.get("SPIFFWORKFLOW_BACKEND_CHECK_FRONTEND_AND_BACKEND_URL_COMPATIBILITY"):
        return

    frontend_url = app.config.get("SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND")
    backend_url = app.config.get("SPIFFWORKFLOW_BACKEND_URL")

    if frontend_url is None or backend_url is None:
        return
    if frontend_url == "" or backend_url == "":
        return
    if not frontend_url.startswith("https://") or not backend_url.startswith("https://"):
        return

    frontend_url_parsed = urlparse(frontend_url)
    frontend_domain = frontend_url_parsed.netloc
    backend_url_parsed = urlparse(backend_url)
    backend_domain = backend_url_parsed.netloc

    if frontend_domain == backend_domain:
        # probably backend and frontend are using different paths.
        # routing by path will work just fine and won't cause any problems with setting cookies
        return

    if backend_domain.endswith(frontend_domain):
        return

    raise ConfigurationError(
        "SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND and SPIFFWORKFLOW_BACKEND_URL are incompatible. We need backend to set"
        " cookies for frontend, so they need to be on the same domain. A common setup is to have frontend on"
        " example.com and backend on api.example.com. If you do not need this functionality, you can avoid this check"
        " by setting environment variable SPIFFWORKFLOW_BACKEND_CHECK_FRONTEND_AND_BACKEND_URL_COMPATIBILITY=false"
    )


def _setup_cipher(app: Flask) -> None:
    encryption_lib = app.config.get("SPIFFWORKFLOW_BACKEND_ENCRYPTION_LIB")
    if encryption_lib not in SUPPORTED_ENCRYPTION_LIBS:
        raise ConfigurationError(
            f"Received invalid encryption lib: {encryption_lib}. Supported libs are {SUPPORTED_ENCRYPTION_LIBS}"
        )

    if encryption_lib == "cryptography":
        from cryptography.fernet import Fernet

        app_secret_key = app.config.get("SPIFFWORKFLOW_BACKEND_ENCRYPTION_KEY")
        if app_secret_key is None:
            raise ConfigurationError(
                "SPIFFWORKFLOW_BACKEND_ENCRYPTION_KEY must be specified if using cryptography encryption lib"
            )

        app_secret_key_bytes = app_secret_key.encode()
        base64_key = base64.b64encode(app_secret_key_bytes)
        fernet_cipher = Fernet(base64_key)
        app.config["CIPHER"] = fernet_cipher

    # no_op_cipher for comparison against possibly-slow encryption libraries
    elif encryption_lib == "no_op_cipher":
        no_op_cipher = NoOpCipher()
        app.config["CIPHER"] = no_op_cipher


def setup_config(app: Flask) -> None:
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config["ENV_IDENTIFIER"] = os.environ.get("SPIFFWORKFLOW_BACKEND_ENV", "local_development")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    load_config_file(app, "spiffworkflow_backend.config.default")

    env_config_prefix = "spiffworkflow_backend.config."
    env_config_module = env_config_prefix + app.config["ENV_IDENTIFIER"]

    load_config_file(app, env_config_module)

    # This allows config/testing.py or instance/config.py to override the default config
    if "ENV_IDENTIFIER" in app.config and app.config["ENV_IDENTIFIER"] in ["testing", "unit_testing"]:
        app.config.from_pyfile(f"config/{app.config['ENV_IDENTIFIER']}.py", silent=True)
    else:
        app.config.from_pyfile(f"{app.instance_path}/config.py", silent=True)

    if app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH"] is None:
        permissions_file_name = app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"]
        if permissions_file_name is not None:
            app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH"] = os.path.join(
                app.root_path,
                "config",
                "permissions",
                permissions_file_name,
            )

    # unversioned (see .gitignore) config that can override everything and include secrets.
    # src/spiffworkflow_backend/config/secrets.py
    app.config.from_pyfile(os.path.join("config", "secrets.py"), silent=True)

    if app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"] is None:
        raise ConfigurationError("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR config must be set")

    if app.config["FLASK_SESSION_SECRET_KEY"] is None:
        raise KeyError("Cannot find the secret_key from the environment. Please set FLASK_SESSION_SECRET_KEY")

    app.secret_key = os.environ.get("FLASK_SESSION_SECRET_KEY")

    app.config["PROCESS_UUID"] = uuid.uuid4()

    setup_database_configs(app)
    setup_logger_for_app(app, logging)
    app.logger.debug(
        f"SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR: {app.config['SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR']}"
    )

    # if git username is defined, default git user email to [username]@users.noreply.github.com
    # that way, you may not have to define both variables in your environment
    git_username = app.config.get("SPIFFWORKFLOW_BACKEND_GIT_USERNAME")
    if git_username and app.config.get("SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL") is None:
        app.config["SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL"] = f"{git_username}@users.noreply.github.com"

    if app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"] == "":
        app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"] = None

    app.config["MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"] = int(
        app.config["SPIFFWORKFLOW_BACKEND_MAX_INSTANCE_LOCK_DURATION_IN_SECONDS"]
    )

    if app.config.get("SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS") is None:
        app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"] = [
            {
                "additional_valid_client_ids": app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_ADDITIONAL_VALID_CLIENT_IDS"),
                "client_id": app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID"),
                "client_secret": app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY"),
                "identifier": "default",
                "internal_uri": app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_INTERNAL_URL"),
                "label": "Default",
                "uri": app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL"),
            }
        ]

    if app.config["SPIFFWORKFLOW_BACKEND_CELERY_ENABLED"]:
        app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND"] = "queue_instructions_for_end_user"
        app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_WEB"] = "queue_instructions_for_end_user"
    else:
        app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND"] = "greedy"
        app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_WEB"] = "run_until_user_message"

    if app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"] is not None:
        if not os.path.isdir(app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"]):
            raise ConfigurationError(
                "Could not find the directory specified with SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH: "
                f"{app.config['SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH']}"
            )

    thread_local_data = threading.local()
    app.config["THREAD_LOCAL_DATA"] = thread_local_data
    _set_up_tenant_specific_fields_as_list_of_strings(app)
    _check_for_incompatible_frontend_and_backend_urls(app)
    _check_extension_api_configs(app)
    _setup_cipher(app)

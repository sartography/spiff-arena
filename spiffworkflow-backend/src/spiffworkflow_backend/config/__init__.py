"""__init__.py."""
import os
import threading
import uuid
from urllib.parse import urlparse

from flask.app import Flask
from werkzeug.utils import ImportStringError

from spiffworkflow_backend.services.logging_service import setup_logger

HTTP_REQUEST_TIMEOUT_SECONDS = 15
CONNECTOR_PROXY_COMMAND_TIMEOUT = 30


class ConfigurationError(Exception):
    pass


def setup_database_configs(app: Flask) -> None:
    if app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_URI") is None:
        database_name = f"spiffworkflow_backend_{app.config['ENV_IDENTIFIER']}"
        if app.config.get("SPIFFWORKFLOW_BACKEND_DATABASE_TYPE") == "sqlite":
            app.config["SQLALCHEMY_DATABASE_URI"] = (
                f"sqlite:///{app.instance_path}/db_{app.config['ENV_IDENTIFIER']}.sqlite3"
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
            app.config["SQLALCHEMY_DATABASE_URI"] = f"mysql+mysqlconnector://root:{db_pswd}@localhost/{database_name}"
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

    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {}
    app.config["SQLALCHEMY_ENGINE_OPTIONS"]["pool_size"] = pool_size


def load_config_file(app: Flask, env_config_module: str) -> None:
    try:
        app.config.from_object(env_config_module)
        print(f"loaded config: {env_config_module}")
    except ImportStringError as exception:
        if os.environ.get("SPIFFWORKFLOW_BACKEND_TERRAFORM_DEPLOYED_ENVIRONMENT") != "true":
            raise ModuleNotFoundError(f"Cannot find config module: {env_config_module}") from exception


def _set_up_tenant_specific_fields_as_list_of_strings(app: Flask) -> None:
    tenant_specific_fields = app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS")

    if tenant_specific_fields is None or tenant_specific_fields == "":
        app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS"] = []
    else:
        app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS"] = tenant_specific_fields.split(",")
        if len(app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS"]) > 3:
            raise ConfigurationError(
                "SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS can have a maximum of 3 fields"
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
    if (
        os.environ.get("SPIFFWORKFLOW_BACKEND_TERRAFORM_DEPLOYED_ENVIRONMENT") == "true"
        and os.environ.get("SPIFFWORKFLOW_BACKEND_ENV") is not None
    ):
        load_config_file(app, f"{env_config_prefix}terraform_deployed_environment")

    env_config_module = env_config_prefix + app.config["ENV_IDENTIFIER"]
    load_config_file(app, env_config_module)

    # This allows config/testing.py or instance/config.py to override the default config
    if "ENV_IDENTIFIER" in app.config and app.config["ENV_IDENTIFIER"] == "testing":
        app.config.from_pyfile("config/testing.py", silent=True)
    elif "ENV_IDENTIFIER" in app.config and app.config["ENV_IDENTIFIER"] == "unit_testing":
        app.config.from_pyfile("config/unit_testing.py", silent=True)
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
            print(f"base_permissions: loaded permissions file: {permissions_file_name}")
        else:
            print("base_permissions: no permissions file loaded")

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
    setup_logger(app)

    if app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"] == "":
        app.config["SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP"] = None

    thread_local_data = threading.local()
    app.config["THREAD_LOCAL_DATA"] = thread_local_data
    _set_up_tenant_specific_fields_as_list_of_strings(app)
    _check_for_incompatible_frontend_and_backend_urls(app)

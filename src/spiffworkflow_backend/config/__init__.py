"""__init__.py."""
import os
import threading

from flask.app import Flask
from spiffworkflow_backend.services.logging_service import setup_logger
from werkzeug.utils import ImportStringError


class ConfigurationError(Exception):
    """ConfigurationError."""


def setup_database_uri(app: Flask) -> None:
    """Setup_database_uri."""
    if os.environ.get("SPIFFWORKFLOW_BACKEND_DATABASE_URI") is None:
        database_name = f"spiffworkflow_backend_{app.config['ENV_IDENTIFIER']}"
        if os.environ.get("SPIFF_DATABASE_TYPE") == "sqlite":
            app.config[
                "SQLALCHEMY_DATABASE_URI"
            ] = f"sqlite:///{app.instance_path}/db_{app.config['ENV_IDENTIFIER']}.sqlite3"
        elif os.environ.get("SPIFF_DATABASE_TYPE") == "postgres":
            app.config[
                "SQLALCHEMY_DATABASE_URI"
            ] = f"postgresql://spiffworkflow_backend:spiffworkflow_backend@localhost:5432/{database_name}"
        else:
            # use pswd to trick flake8 with hardcoded passwords
            db_pswd = os.environ.get("DB_PASSWORD")
            if db_pswd is None:
                db_pswd = ""
            app.config[
                "SQLALCHEMY_DATABASE_URI"
            ] = f"mysql+mysqlconnector://root:{db_pswd}@localhost/{database_name}"
    else:
        app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
            "SPIFFWORKFLOW_BACKEND_DATABASE_URI"
        )


def setup_config(app: Flask) -> None:
    """Setup_config."""
    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    app.config["ENV_IDENTIFIER"] = os.environ.get(
        "SPIFFWORKFLOW_BACKEND_ENV", "development"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config.from_object("spiffworkflow_backend.config.default")

    # This allows config/testing.py or instance/config.py to override the default config
    if "ENV_IDENTIFIER" in app.config and app.config["ENV_IDENTIFIER"] == "testing":
        app.config.from_pyfile("config/testing.py", silent=True)
    else:
        app.config.from_pyfile(f"{app.instance_path}/config.py", silent=True)

    env_config_prefix = "spiffworkflow_backend.config."
    env_config_module = env_config_prefix + app.config["ENV_IDENTIFIER"]
    try:
        app.config.from_object(env_config_module)
    except ImportStringError as exception:
        if (
            os.environ.get("TERRAFORM_DEPLOYED_ENVIRONMENT") == "true"
            and os.environ.get("SPIFFWORKFLOW_BACKEND_ENV") is not None
        ):
            app.config.from_object("{env_config_prefix}terraform_deployed_environment")
        else:
            raise ModuleNotFoundError(
                f"Cannot find config module: {env_config_module}"
            ) from exception

    setup_database_uri(app)
    setup_logger(app)

    app.config["PERMISSIONS_FILE_FULLPATH"] = None
    if app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"]:
        app.config["PERMISSIONS_FILE_FULLPATH"] = os.path.join(
            app.root_path,
            "config",
            "permissions",
            app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"],
        )

    # unversioned (see .gitignore) config that can override everything and include secrets.
    # src/spiffworkflow_backend/config/secrets.py
    app.config.from_pyfile(os.path.join("config", "secrets.py"), silent=True)

    if app.config["BPMN_SPEC_ABSOLUTE_DIR"] is None:
        raise ConfigurationError("BPMN_SPEC_ABSOLUTE_DIR config must be set")

    thread_local_data = threading.local()
    app.config["THREAD_LOCAL_DATA"] = thread_local_data

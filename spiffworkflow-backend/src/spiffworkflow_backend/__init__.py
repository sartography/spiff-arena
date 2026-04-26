import faulthandler
import os
from functools import partial
from typing import Any

import sqlalchemy
from connexion import FlaskApp
from connexion.middleware import MiddlewarePosition
from flask.json.provider import DefaultJSONProvider
from starlette.middleware.cors import CORSMiddleware

import spiffworkflow_backend.load_database_models  # noqa: F401
from spiffworkflow_backend.background_processing.apscheduler import start_apscheduler_if_appropriate
from spiffworkflow_backend.background_processing.celery import init_celery_if_appropriate
from spiffworkflow_backend.config import setup_config
from spiffworkflow_backend.exceptions.api_error import handle_exception
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.db import migrate
from spiffworkflow_backend.routes.authentication_controller import _set_new_access_token_in_cookie
from spiffworkflow_backend.routes.authentication_controller import omni_auth
from spiffworkflow_backend.routes.openid_blueprint.openid_blueprint import openid_blueprint
from spiffworkflow_backend.routes.user_blueprint import user_blueprint
from spiffworkflow_backend.services.monitoring_service import configure_sentry
from spiffworkflow_backend.services.monitoring_service import setup_prometheus_metrics
from spiffworkflow_backend.utils.api_logging import setup_deferred_logging
from spiffworkflow_backend.utils.api_logging import setup_global_api_logging

# This commented out code is if you want to use the pymysql library with sqlalchemy rather than mysqlclient.
# mysqlclient can be hard to install when running non-docker local dev, but it is generally worth it because it is much faster.
# See the repo's top-level README and the linked troubleshooting guide for details.
# import pymysql;
# pymysql.install_as_MySQLdb()


class MyJSONEncoder(DefaultJSONProvider):
    def default(self, obj: Any) -> Any:
        if hasattr(obj, "serialized"):
            return obj.serialized()
        elif isinstance(obj, sqlalchemy.engine.row.Row):  # type: ignore
            return_dict = {}
            row_mapping = obj._mapping
            for row_key in row_mapping.keys():
                row_value = row_mapping[row_key]
                if hasattr(row_value, "serialized"):
                    return_dict.update(row_value.serialized())
                elif hasattr(row_value, "__dict__"):
                    return_dict.update(row_value.__dict__)
                else:
                    return_dict.update({row_key: row_value})
            if "_sa_instance_state" in return_dict:
                return_dict.pop("_sa_instance_state")
            return return_dict
        return super().default(obj)

    def dumps(self, obj: Any, **kwargs: Any) -> Any:
        kwargs.setdefault("default", self.default)
        return super().dumps(obj, **kwargs)


def create_app_for_flask() -> Any:
    return create_app().app


def create_app() -> FlaskApp:
    faulthandler.enable()

    # We need to create the sqlite database in a known location.
    # If we rely on the app.instance_path without setting an environment
    # variable, it will be one thing when we run flask db upgrade in the
    # noxfile and another thing when the tests actually run.
    # instance_path is described more at https://flask.palletsprojects.com/en/2.1.x/config/
    connexion_app = FlaskApp(__name__, server_args={"instance_path": os.environ.get("FLASK_INSTANCE_PATH")})
    app = connexion_app.app
    if app is None:
        raise Exception("Could not find app in FlaskApp")
    app.config["CONNEXION_APP"] = connexion_app
    app.config["SESSION_TYPE"] = "filesystem"
    setup_prometheus_metrics(connexion_app)

    setup_config(app)
    db.init_app(app)
    migrate.init_app(app, db)
    setup_deferred_logging(app)
    setup_global_api_logging(app)

    connexion_app.add_error_handler(Exception, partial(handle_exception, app))

    app.register_blueprint(user_blueprint)

    # only register the backend openid server if the backend is configured to use it
    backend_auths = app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"]
    if len(backend_auths) == 1 and backend_auths[0]["uri"] == f"{app.config['SPIFFWORKFLOW_BACKEND_URL']}/openid":
        app.register_blueprint(openid_blueprint, url_prefix=app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_PATH_PREFIX"])

    # preflight options requests will be allowed if they meet the requirements of the url regex.
    # we will add an Access-Control-Max-Age header to the response to tell the browser it doesn't
    # need to continually keep asking for the same path.
    origins_re_list = [
        r"^https?:\/\/%s(.*)" % o.replace(".", r"\.")  # noqa: UP031
        for o in app.config["SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS"]
    ]
    origin_regex = "|".join(origins_re_list)
    connexion_app.add_middleware(
        CORSMiddleware,
        position=MiddlewarePosition.BEFORE_EXCEPTION,
        allow_origin_regex=origin_regex,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        max_age=3600,
    )

    connexion_app.add_api("api.yml", base_path=app.config["SPIFFWORKFLOW_BACKEND_API_PATH_PREFIX"])

    app.json = MyJSONEncoder(app)

    configure_sentry(app)

    app.before_request(omni_auth)
    app.after_request(_set_new_access_token_in_cookie)

    # The default is true, but we want to preserve the order of keys in the json
    # This is particularly helpful for forms that are generated from json schemas.
    app.json.sort_keys = False

    start_apscheduler_if_appropriate(app)
    init_celery_if_appropriate(app)

    return connexion_app

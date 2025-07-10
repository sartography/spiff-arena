# noqa
import os
import shutil
from collections.abc import Generator
from typing import Any

import flask
import pytest
import starlette
from connexion import FlaskApp
from flask import Flask

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

# We need to call this before importing spiffworkflow_backend
# otherwise typeguard cannot work. hence the noqa: E402
if os.environ.get("RUN_TYPEGUARD") == "true":
    from typeguard import install_import_hook

    install_import_hook(packages="spiffworkflow_backend")


from spiffworkflow_backend import create_app  # noqa: E402


def _set_unit_testing_env_variables() -> None:
    os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "unit_testing"
    os.environ["FLASK_SESSION_SECRET_KEY"] = "e7711a3ba96c46c68e084a86952de16f"  # noqa: S105, do not care about security when running unit tests


@pytest.fixture(scope="session")
def connexion_app() -> Generator[FlaskApp, Any, Any]:  # noqa
    _set_unit_testing_env_variables()
    connexion_app = create_app()
    with connexion_app.app.app_context():
        # to screw with this, poet add nplusone --group dev
        # from nplusone.ext.flask_sqlalchemy import NPlusOne
        # connexion_app.config["NPLUSONE_RAISE"] = True
        # NPlusOne(connexion_app)

        yield connexion_app


@pytest.fixture(scope="session")
def app(connexion_app: FlaskApp) -> Generator[Flask, Any, Any]:  # noqa
    yield connexion_app.app


@pytest.fixture(scope="session")
def client(connexion_app: FlaskApp) -> starlette.testclient.TestClient:  # noqa
    return connexion_app.test_client(follow_redirects=False, base_url="http://localhost")


@pytest.fixture()
def with_db_and_bpmn_file_cleanup() -> Generator[None, Any, Any]:
    """Do it cleanly!"""
    meta = db.metadata
    db.session.execute(db.update(BpmnProcessModel).values(top_level_process_id=None))
    db.session.execute(db.update(BpmnProcessModel).values(direct_parent_process_id=None))

    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()

    # when g.user gets set and then we clear the db, the user is now deleted and so
    # this fails so reset it
    if hasattr(flask.g, "user") and flask.g.user:
        delattr(flask.g, "user")

    try:
        yield
    finally:
        if os.path.exists(ProcessModelService.root_path()):
            shutil.rmtree(ProcessModelService.root_path())
        db.session.close()


@pytest.fixture()
def with_super_admin_user() -> UserModel:  # noqa
    # this loads all permissions from yaml everytime this function is called which is slow
    # so default to just setting a simple super admin and only run with the "real" permissions in ci
    if os.environ.get("SPIFFWORKFLOW_BACKEND_RUNNING_IN_CI") == "true":
        user = BaseTest.find_or_create_user(username="testadmin1")
        AuthorizationService.import_permissions_from_yaml_file(user)
    else:
        user = BaseTest.create_user_with_permission("super_admin")
    return user

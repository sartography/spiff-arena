# noqa
import os
import shutil

import pytest
from flask.app import Flask
from nplusone.ext.flask_sqlalchemy import NPlusOne
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


@pytest.fixture(scope="session")
def app() -> Flask:  # noqa
    os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "unit_testing"
    os.environ["FLASK_SESSION_SECRET_KEY"] = (
        "e7711a3ba96c46c68e084a86952de16f"  # noqa: S105, do not care about security when running unit tests
    )
    app = create_app()

    # commented out because this fails in: test_returns_403_if_user_does_not_have_permission
    # and test_task_models_of_parent_bpmn_processes_stop_on_first_call_activity (maybe just flaky)
    app.config["NPLUSONE_RAISE"] = True
    NPlusOne(app)

    return app


@pytest.fixture()
def with_db_and_bpmn_file_cleanup() -> None:
    """Do it cleanly!"""
    meta = db.metadata
    db.session.execute(db.update(BpmnProcessModel).values(top_level_process_id=None))
    db.session.execute(db.update(BpmnProcessModel).values(direct_parent_process_id=None))

    for table in reversed(meta.sorted_tables):
        db.session.execute(table.delete())
    db.session.commit()

    try:
        yield
    finally:
        if os.path.exists(ProcessModelService.root_path()):
            shutil.rmtree(ProcessModelService.root_path())


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

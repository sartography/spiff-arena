"""Conftest."""
import os
import shutil

import pytest
from flask.app import Flask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService


# We need to call this before importing spiffworkflow_backend
# otherwise typeguard cannot work. hence the noqa: E402
if os.environ.get("RUN_TYPEGUARD") == "true":
    from typeguard import install_import_hook

    install_import_hook(packages="spiffworkflow_backend")


from spiffworkflow_backend import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app() -> Flask:
    """App."""
    os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "unit_testing"
    os.environ["FLASK_SESSION_SECRET_KEY"] = "e7711a3ba96c46c68e084a86952de16f"
    app = create_app()

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
        process_model_service = ProcessModelService()
        if os.path.exists(process_model_service.root_path()):
            shutil.rmtree(process_model_service.root_path())


@pytest.fixture()
def with_super_admin_user() -> UserModel:
    """With_super_admin_user."""
    return BaseTest.create_user_with_permission("super_admin")

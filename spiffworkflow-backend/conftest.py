"""Conftest."""
import os
import shutil

import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.active_task_user import ActiveTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService

# from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


# We need to call this before importing spiffworkflow_backend
# otherwise typeguard cannot work. hence the noqa: E402
if os.environ.get("RUN_TYPEGUARD") == "true":
    from typeguard.importhook import install_import_hook

    install_import_hook(packages="spiffworkflow_backend")


from spiffworkflow_backend import create_app  # noqa: E402


@pytest.fixture(scope="session")
def app() -> Flask:
    """App."""
    os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "testing"
    os.environ["FLASK_SESSION_SECRET_KEY"] = "super_secret_key"
    app = create_app()

    return app


@pytest.fixture()
def with_db_and_bpmn_file_cleanup() -> None:
    """Process_group_resource."""
    db.session.query(ActiveTaskUserModel).delete()

    for model in SpiffworkflowBaseDBModel._all_subclasses():
        db.session.query(model).delete()
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


@pytest.fixture()
def setup_process_instances_for_reports(
    client: FlaskClient, with_super_admin_user: UserModel
) -> list[ProcessInstanceModel]:
    """Setup_process_instances_for_reports."""
    user = with_super_admin_user
    process_group_id = "runs_without_input"
    process_model_id = "sample"
    # bpmn_file_name = "sample.bpmn"
    bpmn_file_location = "sample"
    process_model_identifier = BaseTest().basic_test_setup(
        client,
        with_super_admin_user,
        process_group_id=process_group_id,
        process_model_id=process_model_id,
        # bpmn_file_name=bpmn_file_name,
        bpmn_file_location=bpmn_file_location,
    )

    # BaseTest().create_process_group(
    #     client=client, user=user, process_group_id=process_group_id, display_name=process_group_id
    # )
    # process_model_id = "runs_without_input/sample"
    # load_test_spec(
    #     process_model_id=f"{process_group_id}/{process_model_id}",
    #     process_model_source_directory="sample"
    # )
    process_instances = []
    for data in [kay(), ray(), jay()]:
        process_instance = ProcessInstanceService.create_process_instance(
            # process_group_identifier=process_group_id,
            process_model_identifier=process_model_identifier,
            user=user,
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.slam_in_data(data)
        process_instance.status = "complete"
        db.session.add(process_instance)
        db.session.commit()

        process_instances.append(process_instance)

    return process_instances


def kay() -> dict:
    """Kay."""
    return {"name": "kay", "grade_level": 2, "test_score": 10}


def ray() -> dict:
    """Ray."""
    return {"name": "ray", "grade_level": 1, "test_score": 9}


def jay() -> dict:
    """Jay."""
    return {"name": "jay", "grade_level": 2, "test_score": 8}

"""Test_get_localtime."""
from flask.app import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.process_instance_metadata import (
    ProcessInstanceMetadataModel,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestSaveProcessInstanceMetadata(BaseTest):
    """TestSaveProcessInstanceMetadata."""

    def test_can_save_process_instance_metadata(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_save_process_instance_metadata."""
        self.create_process_group(
            client, with_super_admin_user, "test_group", "test_group"
        )
        process_model = load_test_spec(
            process_model_id="save_process_instance_metadata/save_process_instance_metadata",
            bpmn_file_name="save_process_instance_metadata.bpmn",
            process_model_source_directory="save_process_instance_metadata",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=with_super_admin_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        process_instance_metadata = ProcessInstanceMetadataModel.query.filter_by(
            process_instance_id=process_instance.id
        ).all()
        assert len(process_instance_metadata) == 3

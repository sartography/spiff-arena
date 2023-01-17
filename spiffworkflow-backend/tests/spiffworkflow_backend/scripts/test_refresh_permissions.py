"""Test_get_localtime."""
import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.exceptions.api_error import ApiError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)


class TestRefreshPermissions(BaseTest):
    """TestRefreshPermissions."""

    def test_refresh_permissions_requires_elevated_permission(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_refresh_permissions_requires_elevated_permission."""
        basic_user = self.find_or_create_user("basic_user")
        privileged_user = self.find_or_create_user("privileged_user")
        self.add_permissions_to_user(
            privileged_user,
            target_uri="/can-run-privileged-script/refresh_permissions",
            permission_names=["create"],
        )
        process_model = load_test_spec(
            process_model_id="refresh_permissions",
            process_model_source_directory="script_refresh_permissions",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=basic_user
        )

        processor = ProcessInstanceProcessor(process_instance)

        with pytest.raises(ApiError) as exception:
            processor.do_engine_steps(save=True)
            assert "ScriptUnauthorizedForUserError" in str(exception)

        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=privileged_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == "complete"

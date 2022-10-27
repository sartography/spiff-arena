"""Test_message_service."""
import os

import pytest
from flask import Flask
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from spiffworkflow_backend.models.bpmn_process_id_lookup import BpmnProcessIdLookup
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestSpecFileService(BaseTest):
    """TestSpecFileService."""

    call_activity_nested_relative_file_path = os.path.join(
        "test_process_group_id", "call_activity_nested", "call_activity_nested.bpmn"
    )

    def test_can_store_process_ids_for_lookup(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_can_store_process_ids_for_lookup."""
        load_test_spec(
            "call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )
        bpmn_process_id_lookups = BpmnProcessIdLookup.query.all()
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].bpmn_process_identifier == "Level1"
        assert (
            bpmn_process_id_lookups[0].bpmn_file_relative_path
            == self.call_activity_nested_relative_file_path
        )

    def test_fails_to_save_duplicate_process_id(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_fails_to_save_duplicate_process_id."""
        bpmn_process_identifier = "Level1"
        load_test_spec(
            "call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )
        bpmn_process_id_lookups = BpmnProcessIdLookup.query.all()
        assert len(bpmn_process_id_lookups) == 1
        assert (
            bpmn_process_id_lookups[0].bpmn_process_identifier
            == bpmn_process_identifier
        )
        assert (
            bpmn_process_id_lookups[0].bpmn_file_relative_path
            == self.call_activity_nested_relative_file_path
        )
        with pytest.raises(ApiError) as exception:
            load_test_spec(
                "call_activity_nested_duplicate",
                process_model_source_directory="call_activity_duplicate",
                bpmn_file_name="call_activity_nested_duplicate",
            )
        assert f"Process id ({bpmn_process_identifier}) has already been used" in str(
            exception.value
        )

    def test_updates_relative_file_path_when_appropriate(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_updates_relative_file_path_when_appropriate."""
        bpmn_process_identifier = "Level1"
        bpmn_file_relative_path = os.path.join(
            "test_process_group_id", "call_activity_nested", "new_bpmn_file.bpmn"
        )
        process_id_lookup = BpmnProcessIdLookup(
            bpmn_process_identifier=bpmn_process_identifier,
            bpmn_file_relative_path=bpmn_file_relative_path,
        )
        db.session.add(process_id_lookup)
        db.session.commit()

        load_test_spec(
            "call_activity_nested",
            process_model_source_directory="call_activity_nested",
            bpmn_file_name="call_activity_nested",
        )
        bpmn_process_id_lookups = BpmnProcessIdLookup.query.all()
        assert len(bpmn_process_id_lookups) == 1
        assert (
            bpmn_process_id_lookups[0].bpmn_process_identifier
            == bpmn_process_identifier
        )
        assert (
            bpmn_process_id_lookups[0].bpmn_file_relative_path
            == self.call_activity_nested_relative_file_path
        )

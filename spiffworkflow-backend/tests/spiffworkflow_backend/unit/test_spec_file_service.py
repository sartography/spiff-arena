"""Test_message_service."""
import os

import pytest
from flask import Flask
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser  # type: ignore
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.bpmn_process_id_lookup import BpmnProcessIdLookup
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


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

    def test_load_reference_information(
        self, app: Flask, with_db_and_bpmn_file_cleanup: None
    ) -> None:
        """Test_load_reference_information.

        When getting files from the spec_file service, each file includes
        details about how the file can be referenced -- for instance
        it is possible to reference a DMN file with a Decision.id or
        a bpmn file with a process.id.  These Decisions and processes
        can also have human readable display names, which should also be avaiable.
        Note that a single bpmn file can contain many processes, and
        a DMN file can (theoretically) contain many decisions.  So this
        is an array.
        """
        load_test_spec(
            "call_activity_nested",
            process_model_source_directory="call_activity_nested",
        )
        process_model_info = ProcessModelService().get_process_model(
            "call_activity_nested"
        )
        files = SpecFileService.get_files(process_model_info)

        file = next(filter(lambda f: f.name == "call_activity_level_3.bpmn", files))
        ca_3 = SpecFileService.get_references_for_file(
            file, process_model_info, BpmnDmnParser
        )
        assert len(ca_3) == 1
        assert ca_3[0].name == "Level 3"
        assert ca_3[0].id == "Level3"
        assert ca_3[0].type == "process"

        file = next(filter(lambda f: f.name == "level2c.dmn", files))
        dmn1 = SpecFileService.get_references_for_file(
            file, process_model_info, BpmnDmnParser
        )
        assert len(dmn1) == 1
        assert dmn1[0].name == "Decision 1"
        assert dmn1[0].id == "Decision_0vrtcmk"
        assert dmn1[0].type == "decision"

"""Test_message_service."""
import os

import pytest
from flask import Flask
from flask.testing import FlaskClient
from flask_bpmn.models.db import db
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore
from spiffworkflow_backend.models.spec_reference import SpecReferenceCache
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestSpecFileService(BaseTest):
    """TestSpecFileService."""

    process_group_id = "test_process_group_id"
    process_model_id = "call_activity_nested"
    bpmn_file_name = "call_activity_nested.bpmn"

    call_activity_nested_relative_file_path = os.path.join(
        process_group_id, process_model_id, bpmn_file_name
    )

    def test_can_store_process_ids_for_lookup(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_can_store_process_ids_for_lookup."""
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id=self.process_group_id,
            process_model_id=self.process_model_id,
            bpmn_file_name=self.bpmn_file_name,
            bpmn_file_location="call_activity_nested",
        )
        bpmn_process_id_lookups = SpecReferenceCache.query.all()
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == "Level1"
        assert (
            bpmn_process_id_lookups[0].relative_path
            == self.call_activity_nested_relative_file_path
        )

    def test_fails_to_save_duplicate_process_id(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_fails_to_save_duplicate_process_id."""
        bpmn_process_identifier = "Level1"
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id=self.process_group_id,
            process_model_id=self.process_model_id,
            bpmn_file_name=self.bpmn_file_name,
            bpmn_file_location=self.process_model_id,
        )
        bpmn_process_id_lookups = SpecReferenceCache.query.all()
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == bpmn_process_identifier
        assert (
            bpmn_process_id_lookups[0].relative_path
            == self.call_activity_nested_relative_file_path
        )
        with pytest.raises(ValidationException) as exception:
            load_test_spec(
                "call_activity_nested_duplicate",
                process_model_source_directory="call_activity_duplicate",
                bpmn_file_name="call_activity_nested_duplicate",
            )
            assert (
                f"Process id ({bpmn_process_identifier}) has already been used"
                in str(exception.value)
            )

    def test_updates_relative_file_path_when_appropriate(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_updates_relative_file_path_when_appropriate."""
        bpmn_process_identifier = "Level1"
        process_id_lookup = SpecReferenceCache(
            identifier=bpmn_process_identifier,
            relative_path=self.call_activity_nested_relative_file_path,
            type="process",
        )
        db.session.add(process_id_lookup)
        db.session.commit()

        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id=self.process_group_id,
            process_model_id=self.process_model_id,
            bpmn_file_name=self.bpmn_file_name,
            bpmn_file_location=self.process_model_id,
        )

        bpmn_process_id_lookups = SpecReferenceCache.query.all()
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == bpmn_process_identifier
        assert (
            bpmn_process_id_lookups[0].relative_path
            == self.call_activity_nested_relative_file_path
        )

    def test_change_the_identifier_cleans_up_cache(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """When a BPMN processes identifier is changed in a file, the old id is removed from the cache."""
        old_identifier = "ye_old_identifier"
        process_id_lookup = SpecReferenceCache(
            identifier=old_identifier,
            relative_path=self.call_activity_nested_relative_file_path,
            file_name=self.bpmn_file_name,
            process_model_id=f"{self.process_group_id}/{self.process_model_id}",
            type="process",
        )
        db.session.add(process_id_lookup)
        db.session.commit()

        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id=self.process_group_id,
            process_model_id=self.process_model_id,
            bpmn_file_name=self.bpmn_file_name,
            bpmn_file_location=self.process_model_id,
        )

        bpmn_process_id_lookups = SpecReferenceCache.query.all()
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier != old_identifier
        assert bpmn_process_id_lookups[0].identifier == "Level1"
        assert (
            bpmn_process_id_lookups[0].relative_path
            == self.call_activity_nested_relative_file_path
        )

    def test_load_reference_information(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
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
        process_group_id = "test_group"
        process_model_id = "call_activity_nested"
        process_model_identifier = self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            # bpmn_file_name=bpmn_file_name,
            bpmn_file_location=process_model_id,
        )
        # load_test_spec(
        #     ,
        #     process_model_source_directory="call_activity_nested",
        # )
        process_model_info = ProcessModelService().get_process_model(
            process_model_identifier
        )
        files = SpecFileService.get_files(process_model_info)

        file = next(filter(lambda f: f.name == "call_activity_level_3.bpmn", files))
        ca_3 = SpecFileService.get_references_for_file(file, process_model_info)
        assert len(ca_3) == 1
        assert ca_3[0].display_name == "Level 3"
        assert ca_3[0].identifier == "Level3"
        assert ca_3[0].type == "process"

        file = next(filter(lambda f: f.name == "level2c.dmn", files))
        dmn1 = SpecFileService.get_references_for_file(file, process_model_info)
        assert len(dmn1) == 1
        assert dmn1[0].display_name == "Decision 1"
        assert dmn1[0].identifier == "Decision_0vrtcmk"
        assert dmn1[0].type == "decision"

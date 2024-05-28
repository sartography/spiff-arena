import os
import sys

import pytest
from flask import Flask
from flask.testing import FlaskClient
from lxml import etree  # type: ignore
from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_caller_relationship import ProcessCallerRelationshipModel
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService
from spiffworkflow_backend.services.spec_file_service import ProcessModelFileInvalidError
from spiffworkflow_backend.services.spec_file_service import SpecFileService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestSpecFileService(BaseTest):
    process_group_id = ""
    process_model_id = "test_process_group_id/call_activity_nested"
    # process_group_id = "test_process_group_id"
    # process_model_id = "call_activity_nested"
    bpmn_file_name = "call_activity_nested.bpmn"

    call_activity_nested_relative_file_path = os.path.join(process_model_id, bpmn_file_name)

    def test_can_store_process_ids_for_lookup(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        load_test_spec(
            process_model_id=self.process_model_id,
            process_model_source_directory="call_activity_nested",
        )
        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == "Level1"
        assert bpmn_process_id_lookups[0].relative_path() == self.call_activity_nested_relative_file_path

    def test_fails_to_save_duplicate_process_id_in_same_process_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn_process_identifier = "Level1"
        load_test_spec(
            process_model_id="call_activity_duplicate",
            process_model_source_directory="call_activity_nested",
        )
        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == bpmn_process_identifier
        with pytest.raises(ProcessModelFileInvalidError) as exception:
            load_test_spec(
                process_model_id="call_activity_duplicate",
                process_model_source_directory="call_activity_duplicate",
                bpmn_file_name="call_activity_nested_duplicate",
            )
        assert f"Process id ({bpmn_process_identifier}) has already been used" in str(exception.value)

        process_model = ProcessModelService.get_process_model("call_activity_duplicate")
        full_file_path = SpecFileService.full_file_path(process_model, "call_activity_nested_duplicate.bpmn")
        assert not os.path.isfile(full_file_path)

    def test_updates_relative_file_path_when_appropriate(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        bpmn_process_identifier = "Level1"
        process_id_lookup = ReferenceCacheModel.from_params(
            identifier=bpmn_process_identifier,
            display_name="WHO CARES",
            relative_location=self.process_model_id,
            file_name=self.bpmn_file_name,
            type="process",
            use_current_cache_generation=True,
        )
        db.session.add(process_id_lookup)
        db.session.commit()

        load_test_spec(
            process_model_id=self.process_model_id,
            process_model_source_directory="call_activity_nested",
        )

        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == bpmn_process_identifier
        assert bpmn_process_id_lookups[0].relative_path() == self.call_activity_nested_relative_file_path

    # this is really a test of your configuration.
    # sqlite and postgres are case sensitive by default,
    # but mysql is not, and our app requires that it be.
    def test_database_is_case_sensitive(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_id_lookup = ReferenceCacheModel.from_params(
            identifier="HOT",
            display_name="WHO CARES",
            relative_location=self.process_model_id,
            file_name=self.bpmn_file_name,
            type="process",
            use_current_cache_generation=True,
        )
        db.session.add(process_id_lookup)
        db.session.commit()
        process_id_lookup = ReferenceCacheModel.from_params(
            identifier="hot",
            display_name="WHO CARES",
            relative_location=self.process_model_id,
            file_name=self.bpmn_file_name,
            type="process",
            use_current_cache_generation=True,
        )
        db.session.add(process_id_lookup)
        db.session.commit()

    def test_change_the_identifier_cleans_up_cache(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """When a BPMN processes identifier is changed in a file, the old id is removed from the cache."""
        old_identifier = "ye_old_identifier"
        new_identifier = "Level1"
        process_id_lookup = ReferenceCacheModel.from_params(
            identifier=old_identifier,
            display_name="WHO CARES",
            relative_location=self.process_model_id,
            file_name=self.bpmn_file_name,
            type="process",
            use_current_cache_generation=True,
        )
        db.session.add(process_id_lookup)
        db.session.commit()

        load_test_spec(
            process_model_id=self.process_model_id,
            process_model_source_directory="call_activity_nested",
        )

        old_reference_count = ReferenceCacheModel.basic_query().filter_by(identifier=old_identifier).count()
        assert old_reference_count == 0
        current_references = (
            ReferenceCacheModel.basic_query()
            .filter_by(
                relative_location=self.process_model_id,
                file_name=self.bpmn_file_name,
            )
            .all()
        )
        assert len(current_references) == 1
        assert current_references[0].identifier == new_identifier
        assert current_references[0].relative_path() == self.call_activity_nested_relative_file_path

    def test_load_reference_information(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
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
        process_model_id = "test_group/call_activity_nested"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="call_activity_nested",
        )
        files = SpecFileService.get_files(process_model)

        file = next(filter(lambda f: f.name == "call_activity_level_3.bpmn", files))
        ca_3 = SpecFileService.get_references_for_file(file, process_model)
        assert len(ca_3) == 1
        assert ca_3[0].display_name == "Level 3"
        assert ca_3[0].identifier == "Level3"
        assert ca_3[0].type == "process"

        file = next(filter(lambda f: f.name == "level2c.dmn", files))
        dmn1 = SpecFileService.get_references_for_file(file, process_model)
        assert len(dmn1) == 1
        assert dmn1[0].display_name == "Decision 1"
        assert dmn1[0].identifier == "Decision_0vrtcmk"
        assert dmn1[0].type == "decision"

    def test_validate_bpmn_xml_with_invalid_xml(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="group/invalid_xml",
            bpmn_file_name="script_error_with_task_data.bpmn",
            process_model_source_directory="error",
        )
        with pytest.raises(ProcessModelFileInvalidError):
            SpecFileService.update_file(process_model, "bad_xml.bpmn", b"THIS_IS_NOT_VALID_XML")

        full_file_path = SpecFileService.full_file_path(process_model, "bad_xml.bpmn")
        assert not os.path.isfile(full_file_path)

    def test_uses_correct_cache_generation(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        current_cache_generation = CacheGenerationModel.newest_generation_for_table("reference_cache")
        assert current_cache_generation is None

        load_test_spec(
            process_model_id=self.process_model_id,
            process_model_source_directory="call_activity_nested",
        )
        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == "Level1"
        assert bpmn_process_id_lookups[0].relative_path() == self.call_activity_nested_relative_file_path

        current_cache_generation = CacheGenerationModel.newest_generation_for_table("reference_cache")
        assert current_cache_generation is not None
        assert bpmn_process_id_lookups[0].generation_id == current_cache_generation.id

        # make sure it doesn't add a new entry to the cache
        load_test_spec(
            process_model_id=self.process_model_id,
            process_model_source_directory="call_activity_nested",
        )
        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == "Level1"
        assert bpmn_process_id_lookups[0].relative_path() == self.call_activity_nested_relative_file_path
        assert bpmn_process_id_lookups[0].generation_id == current_cache_generation.id

        cache_generations = CacheGenerationModel.query.all()
        assert len(cache_generations) == 1

        new_cache_generation = CacheGenerationModel(cache_table="reference_cache")
        db.session.add(new_cache_generation)
        db.session.commit()

        cache_generations = CacheGenerationModel.query.all()
        assert len(cache_generations) == 2
        current_cache_generation = CacheGenerationModel.newest_generation_for_table("reference_cache")
        assert current_cache_generation is not None

        load_test_spec(
            process_model_id=self.process_model_id,
            process_model_source_directory="call_activity_nested",
        )
        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 1
        assert bpmn_process_id_lookups[0].identifier == "Level1"
        assert bpmn_process_id_lookups[0].generation_id == current_cache_generation.id

    def test_can_correctly_clear_caches_for_a_file(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        load_test_spec(
            process_model_id=self.process_model_id,
            process_model_source_directory="call_activity_nested",
        )
        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 1
        reference = bpmn_process_id_lookups[0]
        assert reference.identifier == "Level1"
        assert reference.relative_path() == self.call_activity_nested_relative_file_path

        # ensure we add and remove from this table
        process_caller_relationships = ProcessCallerRelationshipModel.query.all()
        assert len(process_caller_relationships) == 4

        process_model = ProcessModelService.get_process_model(reference.relative_location)
        assert process_model is not None
        SpecFileService.clear_caches_for_item(file_name=reference.file_name, process_model_info=process_model)
        db.session.commit()

        bpmn_process_id_lookups = ReferenceCacheService.get_reference_cache_entries_calling_process(["Level2"])
        assert len(bpmn_process_id_lookups) == 0

        process_caller_relationships = ProcessCallerRelationshipModel.query.all()
        assert len(process_caller_relationships) == 2

    @pytest.mark.skipif(
        sys.platform == "win32",
        reason="tmp file path is not valid xml for windows and it doesn't matter",
    )
    def test_does_not_evaluate_entities(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        string_replacement = b"THIS_STRING_SHOULD_NOT_EXIST_ITS_SECRET"
        tmp_file = os.path.normpath(self.get_test_data_file_full_path("file_to_inject", "xml_with_entity"))
        file_contents = self.get_test_data_file_contents("invoice.bpmn", "xml_with_entity")
        file_contents = file_contents.decode("utf-8").replace("{{FULL_PATH_TO_FILE}}", tmp_file).encode()
        etree_element = SpecFileService.get_etree_from_xml_bytes(file_contents)
        assert string_replacement not in etree.tostring(etree_element)

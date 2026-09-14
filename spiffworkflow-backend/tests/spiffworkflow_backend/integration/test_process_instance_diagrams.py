import copy
import shutil
import subprocess
from pathlib import Path

import pytest
from flask import Flask
from lxml import etree  # type: ignore
from starlette.testclient import TestClient

from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_instance_diagram_service import ProcessInstanceDiagramService
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstanceDiagrams(BaseTest):
    @pytest.mark.parametrize("variant", ["", "for-me/"])
    @pytest.mark.parametrize("revision", [None, "", "missing-revision"])
    def test_saved_diagram_survives_model_deletion(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        variant: str,
        revision: str | None,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        instance = self.create_process_instance_from_process_model(model, user=with_super_admin_user)
        runtime = ProcessInstanceRuntime(instance)
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        expected = ProcessInstanceDiagramService.get_xml(instance)
        assert 'bpmnElement="Process_HelloWorld"' in expected
        assert 'name="Hot Subprocess"' in expected
        instance.bpmn_version_control_identifier = revision
        db.session.commit()
        (Path(FileSystemService.root_path()) / model.id / "hello_world.bpmn").write_text("Changed after parsing")
        # Resuming and saving a deserialized runtime must retain the snapshot.
        definition_id = instance.bpmn_process_definition_id
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        db.session.expire_all()
        assert instance.bpmn_process_definition_id == definition_id
        assert ProcessInstanceDiagramService.get_xml(instance) == expected

        shutil.rmtree(FileSystemService.root_path())
        ReferenceCacheModel.query.delete()
        db.session.commit()

        response = client.get(
            f"/v1.0/process-instances/{variant}group:hello/{instance.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json()["bpmn_xml_file_contents"] == expected
        assert response.json()["bpmn_xml_file_contents_retrieval_error"] is None

    @pytest.mark.parametrize("change", ["layout", "task"])
    def test_source_versions_are_independent_of_execution_definitions(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        change: str,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        first = self.create_process_instance_from_process_model(model)
        ProcessInstanceRuntime(first).do_engine_steps(save=True, execution_strategy_name="greedy")
        original_xml = ProcessInstanceDiagramService.get_xml(first)
        second = self.create_process_instance_from_process_model(model)
        ProcessInstanceRuntime(second).do_engine_steps(save=True, execution_strategy_name="greedy")
        assert second.bpmn_process_definition_id == first.bpmn_process_definition_id

        filename = Path(FileSystemService.root_path()) / model.id / "hello_world.bpmn"
        document = ProcessModelService.get_etree_from_xml_bytes(filename.read_bytes())
        if change == "layout":
            document.find(".//{http://www.omg.org/spec/DD/20100524/DC}Bounds").set("x", "999")
        else:
            document.find(".//{http://www.omg.org/spec/BPMN/20100524/MODEL}userTask").set("name", "New task name")
        filename.write_bytes(etree.tostring(document))
        third = self.create_process_instance_from_process_model(model)
        ProcessInstanceRuntime(third).do_engine_steps(save=True, execution_strategy_name="greedy")

        assert second.source_manifest_id == first.source_manifest_id
        assert third.source_manifest_id != first.source_manifest_id
        if change == "layout":
            assert third.bpmn_process_definition_id == first.bpmn_process_definition_id
        else:
            assert third.bpmn_process_definition_id != first.bpmn_process_definition_id
        assert ProcessInstanceDiagramService.get_xml(third) != original_xml
        assert ProcessInstanceDiagramService.get_xml(first) == original_xml

    @pytest.mark.parametrize("external_call", [False, True])
    def test_called_process_uses_the_instances_definition_after_cache_and_files_are_removed(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        external_call: bool,
    ) -> None:
        model = load_test_spec(
            "group/nested", primary_file_name="call_activity_nested.bpmn", process_model_source_directory="call_activity_nested"
        )
        if external_call:
            (Path(FileSystemService.root_path()) / model.id / "call_activity_level_2b.bpmn").unlink()
            load_test_spec("group/called", "call_activity_level_2b.bpmn", process_model_source_directory="call_activity_nested")
        instance = self.create_process_instance_from_process_model(model, user=with_super_admin_user)
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        expected = ProcessInstanceDiagramService.get_xml(instance, "Level2b")
        assert 'bpmnElement="Level2b"' in expected
        assert expected != ProcessInstanceDiagramService.get_xml(instance)
        shutil.rmtree(FileSystemService.root_path())
        ReferenceCacheModel.query.delete()
        db.session.commit()

        for process_identifier, xml in [("Level2b", expected), ("unrelated", None), ("Level2b", expected)]:
            response = client.get(
                f"/v1.0/process-instances/group:nested/{instance.id}?process_identifier={process_identifier}",
                headers=self.logged_in_headers(with_super_admin_user),
            )
            assert response.status_code == 200
            assert response.json()["bpmn_xml_file_contents"] == xml
            assert bool(response.json()["bpmn_xml_file_contents_retrieval_error"]) == (xml is None)

    def test_no_git_deployment_captures_the_document_before_files_change(
        self,
        app: Flask,
        client: TestClient,
        monkeypatch: pytest.MonkeyPatch,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        tmp_path: Path,
    ) -> None:
        monkeypatch.setitem(app.config, "SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR", str(tmp_path / "models"))
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        instance, _ = ProcessInstanceService.create_process_instance(model, with_super_admin_user, start_configuration=(0, 0, 0))
        db.session.commit()
        assert instance.bpmn_version_control_identifier is None
        runtime = ProcessInstanceRuntime(instance)
        (Path(FileSystemService.root_path()) / model.id / "hello_world.bpmn").write_text("Changed before execution")
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")

        response = client.get(
            f"/v1.0/process-instances/group:hello/{instance.id}", headers=self.logged_in_headers(with_super_admin_user)
        )
        assert response.status_code == 200
        assert response.json()["bpmn_xml_file_contents_retrieval_error"] is None
        assert 'bpmnElement="Process_HelloWorld"' in response.json()["bpmn_xml_file_contents"]
        assert "Changed before execution" not in response.json()["bpmn_xml_file_contents"]

    @pytest.mark.parametrize("revision", [None, "", "missing-revision"])
    def test_legacy_instance_never_falls_back_to_current_file(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        revision: str | None,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        instance = self.create_process_instance_from_process_model(model, user=with_super_admin_user)
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        definition = instance.bpmn_process_definition
        instance.source_manifest_id = None
        definition.properties_json = {key: value for key, value in definition.properties_json.items() if key != "bpmn_xml"}
        instance.bpmn_version_control_identifier = revision
        db.session.commit()

        response = client.get(
            f"/v1.0/process-instances/group:hello/{instance.id}", headers=self.logged_in_headers(with_super_admin_user)
        )
        assert response.status_code == 200
        assert response.json()["bpmn_xml_file_contents"] is None
        assert response.json()["bpmn_xml_file_contents_retrieval_error"]

    def test_legacy_git_lookup_reads_committed_file_even_at_head_and_after_primary_file_rename(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        instance = self.create_process_instance_from_process_model(model)
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        definition = instance.bpmn_process_definition
        instance.source_manifest_id = None
        definition.properties_json = {key: value for key, value in definition.properties_json.items() if key != "bpmn_xml"}
        definition.properties_json = {**definition.properties_json, "file": "hello_world.bpmn"}
        directory = FileSystemService.root_path()
        for command in [
            ["init"],
            ["add", "."],
            ["-c", "user.name=Tests", "-c", "user.email=tests@example.com", "commit", "-m", "Original"],
        ]:
            subprocess.run(["git", *command], cwd=directory, check=True, capture_output=True)  # noqa: S603, S607
        GitService.clear_current_revision_cache()
        instance.bpmn_version_control_identifier = GitService.get_current_revision()
        db.session.commit()
        filename = Path(directory) / model.id / "hello_world.bpmn"
        original = filename.read_text().strip()
        filename.write_text("Today's uncommitted file")
        model.primary_file_name = "renamed.bpmn"
        ProcessModelService.save_process_model(model)

        assert ProcessInstanceDiagramService.get_xml(instance) == original
        assert "bpmn_xml" not in definition.properties_json  # GET does not backfill or mutate definitions.

    def test_legacy_definition_round_trip_does_not_change_hash_or_attach_current_xml(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        spec, subprocesses = BpmnProcessService.get_process_model_and_subprocesses(model.id)
        workflow = BpmnProcessService.get_bpmn_process_instance_from_workflow_spec(spec, subprocesses)
        serialized = BpmnProcessService.serialize(workflow)
        for spec_dict in [serialized["spec"], *serialized["subprocess_specs"].values()]:
            spec_dict.pop("bpmn_xml", None)
        restored = BpmnProcessService.serializer.from_dict(copy.deepcopy(serialized))
        reserialized = BpmnProcessService.serialize(restored)
        for key in BpmnProcessDefinitionModel.keys_for_full_process_model_hash():
            assert reserialized.get(key) == serialized.get(key)

    def test_uninitialized_instance_has_explicit_unavailable_diagram(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        instance = self.create_process_instance_from_process_model(model, user=with_super_admin_user)
        assert instance.bpmn_process_definition_id is None
        response = client.get(
            f"/v1.0/process-instances/group:hello/{instance.id}", headers=self.logged_in_headers(with_super_admin_user)
        )
        assert response.status_code == 200
        assert response.json()["bpmn_xml_file_contents"] is None
        assert response.json()["bpmn_xml_file_contents_retrieval_error"]

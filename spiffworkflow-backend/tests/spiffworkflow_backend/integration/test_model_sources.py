import shutil
from pathlib import Path

import pytest
from flask import Flask
from lxml import etree  # type: ignore
from starlette.testclient import TestClient

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.model_source import ModelSourceBlobModel
from spiffworkflow_backend.models.model_source import ModelSourceManifestModel
from spiffworkflow_backend.models.process_instance_migration_detail import ProcessInstanceMigrationDetailModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.model_source_service import ModelSourceService
from spiffworkflow_backend.services.model_source_service import ModelSourceUnavailableError
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"


def wrap_in_call_activity(child: ProcessModelInfo) -> ProcessModelInfo:
    parent = load_test_spec("group/parent", "hello_world.bpmn", process_model_source_directory="hello_world")
    filename = Path(FileSystemService.root_path()) / parent.id / "hello_world.bpmn"
    document = ProcessModelService.get_etree_from_xml_bytes(filename.read_bytes())
    task = document.find(f".//{{{BPMN_NS}}}subProcess")
    task.tag = f"{{{BPMN_NS}}}callActivity"
    task.set("calledElement", child.primary_process_id)
    for element in list(task):
        if element.tag not in [f"{{{BPMN_NS}}}incoming", f"{{{BPMN_NS}}}outgoing"]:
            task.remove(element)
    filename.write_bytes(etree.tostring(document))
    return parent


class TestModelSources(BaseTest):
    @pytest.mark.parametrize("called", [False, True])
    @pytest.mark.parametrize("compile_at_creation", [False, True])
    def test_queued_instances_execute_and_serve_the_captured_dmn(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        called: bool,
        compile_at_creation: bool,
    ) -> None:
        child = load_test_spec("group/decision", primary_file_name="sample.bpmn", process_model_source_directory="sample")
        model = wrap_in_call_activity(child) if called else child
        old, _ = ProcessInstanceService.create_process_instance(
            model, with_super_admin_user, start_configuration=(0, 0, 0), load_bpmn_process_model=compile_at_creation
        )
        old.bpmn_version_control_identifier = None
        db.session.commit()
        path = f"{child.id}/wonderful.dmn"
        filename = Path(FileSystemService.root_path()) / path
        original = filename.read_bytes()
        filename.write_bytes(original.replace(b"Very wonderful", b"Changed decision"))
        new, _ = ProcessInstanceService.create_process_instance(model, with_super_admin_user, start_configuration=(0, 0, 0))
        db.session.commit()
        assert new.source_manifest_id != old.source_manifest_id
        shutil.rmtree(FileSystemService.root_path())
        ReferenceCacheModel.query.delete()
        db.session.commit()

        for instance, expected in [(old, "Very wonderful"), (new, "Changed decision")]:
            runtime = ProcessInstanceRuntime(instance)
            runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
            assert runtime.get_current_data()["wonderfulness"] == expected
            for variant in ["", "for-me/"]:
                endpoint = f"/v1.0/process-instances/{variant}{model.id.replace('/', ':')}/{instance.id}"
                response = client.get(endpoint, headers=self.logged_in_headers(with_super_admin_user))
                assert response.status_code == 200
                assert response.json()["decision_source_paths"]["wonderful"] == path
                source = client.get(
                    f"{endpoint}/source-files", params={"path": path}, headers=self.logged_in_headers(with_super_admin_user)
                )
                assert source.status_code == 200
                assert expected in source.json()["file_contents"]
                assert source.json()["encoding"] == "utf-8"
        assert ModelSourceService.read(old.source_manifest_id, path) == original
        assert "bpmn_xml" not in old.bpmn_process_definition.properties_json

    @pytest.mark.parametrize("called", [False, True])
    def test_forms_use_the_saved_schema_and_ui_schema_after_model_deletion(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        called: bool,
    ) -> None:
        child = load_test_spec("group/form", "simple_form.bpmn", process_model_source_directory="simple_form")
        model = wrap_in_call_activity(child) if called else child
        directory = Path(FileSystemService.root_path()) / child.id
        (directory / "simple_form.json").write_text('{"title": "Saved {{ customer }}", "type": "object"}')
        (directory / "simple_form_ui.json").write_text('{"ui:submitButtonOptions": {"submitText": "Original"}}')
        instance, _ = ProcessInstanceService.create_process_instance(model, with_super_admin_user, start_configuration=(0, 0, 0))
        db.session.commit()
        runtime = ProcessInstanceRuntime(instance)
        runtime.bpmn_process_instance.task_tree.set_data(customer="Ada")
        runtime.do_engine_steps(save=True, execution_strategy_name="greedy")
        task = instance.active_human_tasks[0]
        (directory / "simple_form.json").write_text('{"title": "Current form"}')
        (directory / "simple_form_ui.json").unlink()
        shutil.rmtree(FileSystemService.root_path())
        ReferenceCacheModel.query.delete()
        db.session.commit()
        response = client.get(
            f"/v1.0/tasks/{instance.id}/{task.task_id}?with_form_data=true", headers=self.logged_in_headers(with_super_admin_user)
        )
        assert response.status_code == 200
        assert response.json()["form_schema"]["title"] == "Saved Ada"
        assert response.json()["form_ui_schema"]["ui:submitButtonOptions"]["submitText"] == "Original"

    def test_source_only_migrations_pin_an_explicit_version_and_deduplicate_blobs(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        model = load_test_spec("group/form", "simple_form.bpmn", process_model_source_directory="simple_form")
        user = self.find_or_create_user("initiator")
        instance, _ = ProcessInstanceService.create_process_instance(model, user, start_configuration=(0, 0, 0))
        db.session.commit()
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        first_manifest = instance.source_manifest_id
        definition_hash = instance.bpmn_process_definition.full_process_model_hash
        blobs_before = ModelSourceBlobModel.query.count()
        filename = Path(FileSystemService.root_path()) / model.id / "simple_form.json"
        filename.write_text('{"title": "New form", "type": "object"}')
        ProcessInstanceService.migrate_process_instance(instance, user)
        assert instance.source_manifest_id != first_manifest
        assert instance.bpmn_process_definition.full_process_model_hash == definition_hash
        assert ModelSourceBlobModel.query.count() == blobs_before + 1
        assert ModelSourceManifestModel.query.count() == 2
        detail = ProcessInstanceMigrationDetailModel.query.one()
        assert detail.initial_source_manifest_id == first_manifest
        assert detail.target_source_manifest_id == instance.source_manifest_id
        with pytest.raises(ApiError, match="several source versions"):
            ProcessInstanceService.migrate_process_instance(instance, user, target_bpmn_process_hash=definition_hash)
        ProcessInstanceService.migrate_process_instance(
            instance, user, target_bpmn_process_hash=definition_hash, target_source_manifest_id=first_manifest
        )
        assert instance.source_manifest_id == first_manifest

    def test_capture_excludes_live_data_and_includes_declared_shared_assets(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        model = load_test_spec("group/form", "simple_form.bpmn", process_model_source_directory="simple_form")
        root = Path(FileSystemService.root_path())
        model_dir = root / model.id
        bpmn_file = model_dir / "simple_form.bpmn"
        document = ProcessModelService.get_etree_from_xml_bytes(bpmn_file.read_bytes())
        etree.SubElement(document, f"{{{BPMN_NS}}}dataStore", id="records", name="JSONFileDataStore")
        bpmn_file.write_bytes(etree.tostring(document))
        (model_dir / "records.json").write_text('{"mutable": 1}')
        (model_dir / "cache.json").write_text('{"cached": 1}')
        (root / "group/process_group.json").write_text("{}")
        (root / "group/shared.md").write_text("Original shared instructions")
        (model_dir / "logo.png").write_bytes(b"\x89PNG\x00\xff")
        (model_dir / "notes.md").write_text("Original instructions")
        model.source_assets = ["group/shared.md"]
        model.live_data_files = ["cache.json"]
        ProcessModelService.save_process_model(model)
        original = ModelSourceService.capture(model.id)
        (model_dir / "records.json").write_text('{"mutable": 2}')
        (model_dir / "cache.json").write_text('{"cached": 2}')
        assert ModelSourceService.capture(model.id).digest == original.digest
        assert f"{model.id}/records.json" not in original.files
        assert f"{model.id}/cache.json" not in original.files
        assert original.files["group/shared.md"] == b"Original shared instructions"
        assert "group/process_group.json" in original.files
        digest = ModelSourceService.store(original)
        db.session.commit()
        shutil.rmtree(root)
        assert ModelSourceService.read(digest, f"{model.id}/logo.png") == b"\x89PNG\x00\xff"
        for path in ["../outside.json", "/etc/passwd", "group/not-captured.json"]:
            with pytest.raises(ModelSourceUnavailableError):
                ModelSourceService.read(digest, path)

    def test_source_endpoint_checks_instance_ownership_and_manifest_membership(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        model = load_test_spec("group/form", "simple_form.bpmn", process_model_source_directory="simple_form")
        owner = self.find_or_create_user("owner")
        instance, _ = ProcessInstanceService.create_process_instance(model, owner, start_configuration=(0, 0, 0))
        db.session.commit()
        headers = self.logged_in_headers(with_super_admin_user)
        response = client.get(
            f"/v1.0/process-instances/for-me/group:form/{instance.id}/source-files",
            params={"path": "group/form/simple_form.json"},
            headers=headers,
        )
        assert response.status_code == 400
        response = client.get(
            f"/v1.0/process-instances/group:other/{instance.id}/source-files",
            params={"path": "group/form/simple_form.json"},
            headers=headers,
        )
        assert response.status_code == 404
        response = client.get(
            f"/v1.0/process-instances/group:form/{instance.id}/source-files",
            params={"path": "group/other/private.json"},
            headers=headers,
        )
        assert response.status_code == 404

    def test_failed_migration_rolls_back_sources_and_definition_together(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from spiffworkflow_backend.services.task_service import TaskService

        model = load_test_spec("group/form", "simple_form.bpmn", process_model_source_directory="simple_form")
        user = self.find_or_create_user("initiator")
        instance, _ = ProcessInstanceService.create_process_instance(model, user, start_configuration=(0, 0, 0))
        db.session.commit()
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        original_manifest = instance.source_manifest_id
        original_definition = instance.bpmn_process_definition_id
        filename = Path(FileSystemService.root_path()) / model.id / "simple_form.bpmn"
        filename.write_text(filename.read_text().replace('name="Simple Form"', 'name="Changed Form"'))

        def fail_save(*args: object, **kwargs: object) -> None:
            raise RuntimeError("Interrupted migration")

        monkeypatch.setattr(TaskService, "save_objects_to_database", fail_save)
        with pytest.raises(RuntimeError, match="Interrupted migration"):
            ProcessInstanceService.migrate_process_instance(instance, user)
        db.session.rollback()
        assert instance.source_manifest_id == original_manifest
        assert instance.bpmn_process_definition_id == original_definition
        assert ProcessInstanceMigrationDetailModel.query.count() == 0

    def test_capture_retries_when_a_source_changes_while_being_read(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        model = load_test_spec("group/form", "simple_form.bpmn", process_model_source_directory="simple_form")
        original_read = Path.read_bytes
        filename = Path(FileSystemService.root_path()) / model.id / "simple_form.json"
        filename.write_text("{}")
        original = filename.read_bytes()
        updated = b'{"title":"New form"}'

        def read_and_edit(path: Path) -> bytes:
            contents = original_read(path)
            if path == filename and contents == original:
                path.write_bytes(updated)
            return contents

        monkeypatch.setattr(Path, "read_bytes", read_and_edit)
        snapshot = ModelSourceService.capture(model.id)
        assert snapshot.files[f"{model.id}/simple_form.json"] == updated

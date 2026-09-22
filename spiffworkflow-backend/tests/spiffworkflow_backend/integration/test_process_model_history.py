import copy
import shutil
from pathlib import Path
from unittest.mock import Mock

import flask
import pytest
from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.form_schema_service import FormSchemaService
from spiffworkflow_backend.services.message_service import MessageService
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_history import process_model_history
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessModelHistory(BaseTest):
    def test_real_postgres_provider_end_to_end(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        history = process_model_history()
        if history is None or app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] != "postgres":
            pytest.skip("Requires the real history extension and PostgreSQL")
        model = load_test_spec(
            "group/real-history",
            primary_file_name="simple_form.bpmn",
            process_model_source_directory="simple_form",
        )
        model_path = Path(FileSystemService.root_path()) / model.id
        instance, _ = ProcessInstanceService.create_process_instance(model, with_super_admin_user)
        db.session.commit()
        assert history.has_snapshot(instance.id)
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        human_task = HumanTaskModel.query.filter_by(process_instance_id=instance.id).one()
        shutil.rmtree(model_path)

        response = client.get(
            f"/v1.0/tasks/{instance.id}/{human_task.task_id}?with_form_data=true",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json()["form_schema"]["title"] == "Simple form"
        response = client.get(
            f"/v1.0/process-instances/group:real-history/{instance.id}",
            params={"source_file_path": "group/real-history/simple_form.json"},
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json()["source_file"]["encoding"] == "utf-8"

    @pytest.mark.parametrize("variant", ["", "for-me/"])
    def test_capture_deferred_runtime_and_read_delegation(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        monkeypatch: pytest.MonkeyPatch,
        variant: str,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        captured_specs = BpmnProcessService.get_process_model_and_subprocesses(model.id)
        provider = Mock()
        provider.has_snapshot.return_value = True
        provider.capture.side_effect = lambda *args: copy.deepcopy(captured_specs)
        provider.specs.side_effect = lambda *args: copy.deepcopy(captured_specs)
        monkeypatch.setitem(app.extensions, "process_model_history", Mock(return_value=provider))
        with monkeypatch.context() as transaction_patch:
            commit = Mock(wraps=db.session.commit)
            transaction_patch.setattr(db.session, "commit", commit)
            instance, _ = ProcessInstanceService.create_process_instance(
                model, with_super_admin_user, start_configuration=(0, 3600, 0), load_bpmn_process_model=False
            )
            commit.assert_not_called()
        provider.capture.assert_called_once_with(instance.id, model.id)
        response = client.get(
            f"/v1.0/process-instances/group:hello/{instance.id}/check-can-migrate",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 409
        db.session.commit()
        (Path(FileSystemService.root_path()) / model.id / "hello_world.bpmn").write_text("not valid XML")
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        provider.specs.assert_called_with(instance.id, model.id, None)
        provider.instance_payload.return_value = {
            "bpmn_xml_file_contents": "archived XML",
            "bpmn_xml_file_contents_retrieval_error": None,
        }
        response = client.get(
            f"/v1.0/process-instances/{variant}group:hello/{instance.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert response.json()["bpmn_xml_file_contents"] == "archived XML"
        provider.instance_payload.assert_called_with(instance.id, model.id, None)
        expected_file_payload = {
            "path": "image.png",
            "encoding": "base64",
            "file_contents": "iVBORw==",
            "content_type": "image/png",
        }
        provider.file_payload.return_value = expected_file_payload
        endpoint = f"/v1.0/process-instances/{variant}group:hello/{instance.id}"
        response = client.get(
            endpoint, params={"source_file_path": "image.png"}, headers=self.logged_in_headers(with_super_admin_user)
        )
        assert response.status_code == 200
        assert response.json()["source_file"] == expected_file_payload
        provider.file_payload.assert_called_once_with(instance.id, "image.png")
        provider.file_payload.reset_mock()
        response = client.get(
            endpoint.replace("group:hello", "group:wrong"),
            params={"source_file_path": "image.png"},
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 404
        provider.file_payload.assert_not_called()
        if hasattr(flask.g, "user"):
            delattr(flask.g, "user")
        response = client.get(endpoint, params={"source_file_path": "image.png"})
        assert response.status_code in (401, 403)
        provider.file_payload.assert_not_called()
        provider.file_payload.side_effect = FileNotFoundError("not archived")
        response = client.get(
            endpoint, params={"source_file_path": "missing"}, headers=self.logged_in_headers(with_super_admin_user)
        )
        assert response.status_code == 404
        with pytest.raises(ApiError, match="not yet supported"):
            ProcessInstanceService.check_process_instance_can_be_migrated(instance)

    def test_form_uses_archive_after_live_model_is_removed(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        model = load_test_spec(
            "group/simple-form",
            primary_file_name="simple_form.bpmn",
            process_model_source_directory="simple_form",
        )
        model_path = Path(FileSystemService.root_path()) / model.id
        archived_forms = {name: (model_path / name).read_bytes() for name in ("simple_form.json", "simple_form_ui.json")}
        captured_specs = BpmnProcessService.get_process_model_and_subprocesses(model.id)
        provider = Mock()
        provider.has_snapshot.return_value = True
        provider.capture.side_effect = lambda *args: copy.deepcopy(captured_specs)
        provider.specs.side_effect = lambda *args: copy.deepcopy(captured_specs)
        provider.task_file.side_effect = lambda _instance_id, _process_id, filename: archived_forms[filename]
        monkeypatch.setitem(app.extensions, "process_model_history", Mock(return_value=provider))
        instance, _ = ProcessInstanceService.create_process_instance(model, with_super_admin_user)
        db.session.commit()
        ProcessInstanceRuntime(instance).do_engine_steps(save=True, execution_strategy_name="greedy")
        human_task = HumanTaskModel.query.filter_by(process_instance_id=instance.id).one()
        shutil.rmtree(model_path)

        response = client.get(
            f"/v1.0/tasks/{instance.id}/{human_task.task_id}?with_form_data=true",
            headers=self.logged_in_headers(with_super_admin_user),
        )

        assert response.status_code == 200
        assert response.json()["form_schema"]["title"] == "Simple form"
        assert response.json()["form_ui_schema"]["ui:order"] == ["name", "department"]

    def test_reserved_message_start_persists_archived_specs(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        provider = Mock()
        provider.has_snapshot.return_value = True
        archived_specs = (Mock(), Mock())
        provider.specs.return_value = archived_specs
        monkeypatch.setitem(app.extensions, "process_model_history", Mock(return_value=provider))
        persist = Mock()
        monkeypatch.setattr(BpmnProcessService, "persist_bpmn_process_definition", persist)
        monkeypatch.setattr(ProcessInstanceService, "next_start_event_configuration", Mock(return_value=(0, 0, 0)))
        monkeypatch.setattr(ProcessInstanceService, "register_process_model_cycles", Mock())
        instance = Mock(id=42, process_model_identifier="group/message-start")

        MessageService._prepare_reserved_process_for_message_start(instance)

        provider.specs.assert_called_once_with(42, "group/message-start", None)
        persist.assert_called_once_with("group/message-start", specs=archived_specs)

    def test_form_reads_saved_owner_and_does_not_fall_back(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        provider = Mock()
        provider.has_snapshot.return_value = True
        monkeypatch.setitem(app.extensions, "process_model_history", Mock(return_value=provider))
        task = Mock(process_instance_id=123, data=None)
        task.bpmn_process.bpmn_process_definition.bpmn_identifier = "called"
        provider.task_file.return_value = b'{"title":"Saved form"}'
        assert FormSchemaService.prepare_form_data("form.json", Mock(), task) == {"title": "Saved form"}
        provider.task_file.assert_called_with(123, "called", "form.json")
        provider.task_file.side_effect = FileNotFoundError("missing saved form")
        with pytest.raises(ApiError, match="missing saved form"):
            FormSchemaService.prepare_form_data("form.json", Mock(), task)

    def test_capture_failure_does_not_enqueue(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        model = load_test_spec("group/hello", "hello_world.bpmn", process_model_source_directory="hello_world")
        provider = Mock()
        provider.capture.side_effect = ValueError("capture failed")
        monkeypatch.setitem(app.extensions, "process_model_history", Mock(return_value=provider))
        enqueue = Mock()
        monkeypatch.setattr(
            "spiffworkflow_backend.services.process_instance_service.ProcessInstanceQueueService.enqueue_new_process_instance",
            enqueue,
        )
        with pytest.raises(ValueError, match="capture failed"):
            ProcessInstanceService.create_process_instance(model, with_super_admin_user)
        enqueue.assert_not_called()
        db.session.rollback()

    def test_existing_instance_without_snapshot_uses_legacy_behavior(self, app: Flask, monkeypatch: pytest.MonkeyPatch) -> None:
        provider = Mock()
        provider.has_snapshot.return_value = False
        monkeypatch.setitem(app.extensions, "process_model_history", Mock(return_value=provider))

        assert process_model_history() is provider
        assert process_model_history(123) is None
        provider.has_snapshot.assert_called_once_with(123)

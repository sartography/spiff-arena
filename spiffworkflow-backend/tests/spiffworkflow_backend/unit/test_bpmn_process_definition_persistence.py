import importlib.util
from pathlib import Path

from flask import Flask
import pytest

from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


_AUDIT_SCRIPT_PATH = Path(__file__).resolve().parents[3] / "bin" / "audit_process_definitions.py"
_AUDIT_SPEC = importlib.util.spec_from_file_location("audit_process_definitions", _AUDIT_SCRIPT_PATH)
assert _AUDIT_SPEC is not None and _AUDIT_SPEC.loader is not None
_AUDIT_MODULE = importlib.util.module_from_spec(_AUDIT_SPEC)
_AUDIT_SPEC.loader.exec_module(_AUDIT_MODULE)


class TestBpmnProcessDefinitionPersistence(BaseTest):
    def test_persist_bpmn_process_definition_rolls_back_parent_row_when_task_definition_insert_fails(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )

        original_insert = TaskDefinitionModel.insert_or_update_record
        insert_call_count = 0

        def fail_on_first_task_insert(task_definition_dict: dict) -> object:
            nonlocal insert_call_count
            insert_call_count += 1
            if insert_call_count == 1:
                raise RuntimeError("boom during task definition insert")
            return original_insert(task_definition_dict)

        monkeypatch.setattr(TaskDefinitionModel, "insert_or_update_record", fail_on_first_task_insert)

        with pytest.raises(RuntimeError, match="boom during task definition insert"):
            BpmnProcessService.persist_bpmn_process_definition(process_model.id)

        assert BpmnProcessDefinitionModel.query.count() == 0
        assert TaskDefinitionModel.query.count() == 0

    def test_audit_detects_process_model_with_missing_persisted_task_definitions(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/hello_world",
            bpmn_file_name="hello_world.bpmn",
            process_model_source_directory="hello_world",
        )

        BpmnProcessService.persist_bpmn_process_definition(process_model.id)
        persisted_definition = BpmnProcessDefinitionModel.query.filter(
            BpmnProcessDefinitionModel.full_process_model_hash.is_not(None)  # type: ignore
        ).one()
        TaskDefinitionModel.query.filter_by(bpmn_process_definition_id=persisted_definition.id).delete()
        db.session.commit()

        issues = _AUDIT_MODULE.audit_all_process_models()

        assert len(issues) == 1
        assert issues[0]["process_model_id"] == process_model.id
        assert issues[0]["issue"] == "task_definition_count_mismatch"
        assert issues[0]["expected_task_definition_count"] > 0
        assert issues[0]["actual_task_definition_count"] == 0

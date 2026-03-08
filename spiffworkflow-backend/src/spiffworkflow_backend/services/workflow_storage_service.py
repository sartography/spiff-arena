from __future__ import annotations

import copy
import time
from typing import Any
from typing import cast
from uuid import UUID

from flask import current_app
from SpiffWorkflow.bpmn.serializer.helpers.registry import DefaultRegistry  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task import TaskNotFoundError
from spiffworkflow_backend.models.workflow_blob_storage import WorkflowBlobStorageModel
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService


class SyntheticTaskModel:
    def __init__(
        self,
        *,
        guid: str,
        process_instance_id: int,
        task_definition: Any,
        bpmn_process: BpmnProcessModel | None,
        state: str,
        properties_json: dict,
        runtime_info: dict | None,
        task_data: dict | None,
        python_env_data: dict | None,
    ) -> None:
        self.guid = guid
        self.process_instance_id = process_instance_id
        self.task_definition = task_definition
        self.task_definition_id = task_definition.id
        self.bpmn_process = bpmn_process
        self.bpmn_process_id = bpmn_process.id if bpmn_process is not None else None
        self.state = state
        self.properties_json = properties_json
        self.runtime_info = runtime_info
        self._task_data = task_data or {}
        self._python_env_data = python_env_data or {}
        self.start_in_seconds = properties_json.get("last_state_change")
        finished_states = {
            TaskState.get_name(TaskState.COMPLETED),
            TaskState.get_name(TaskState.ERROR),
            TaskState.get_name(TaskState.CANCELLED),
        }
        self.end_in_seconds = properties_json.get("last_state_change") if state in finished_states else None

        # dynamically-populated fields used in request handlers
        self.data: dict | None = None
        self.saved_form_data: dict | None = None
        self.form_schema: dict | None = None
        self.form_ui_schema: dict | None = None
        self.process_model_display_name: str | None = None
        self.process_model_identifier: str | None = None
        self.typename: str | None = None
        self.can_complete: bool | None = None
        self.extensions: dict | None = None
        self.name_for_display: str | None = None
        self.signal_buttons: list[dict] | None = None

    def json_data(self) -> dict:
        return self._task_data

    def python_env_data(self) -> dict:
        return self._python_env_data

    def get_data(self) -> dict:
        return {**self.python_env_data(), **self.json_data()}

    def allows_guest(self, process_instance_id: int) -> bool:
        properties_json = self.task_definition.properties_json
        if (
            "extensions" in properties_json
            and "allowGuest" in properties_json["extensions"]
            and properties_json["extensions"]["allowGuest"] == "true"
            and self.process_instance_id == int(process_instance_id)
            and self.state != "COMPLETED"
        ):
            return True
        return False


class WorkflowStorageService:
    TASK_BASED = "task_based"
    BLOB_BASED = "blob_based"
    SUPPORTED_STRATEGIES = {TASK_BASED, BLOB_BASED}

    @classmethod
    def strategy_for_process_instance(cls, process_instance: ProcessInstanceModel) -> str:
        if process_instance.workflow_storage_strategy in cls.SUPPORTED_STRATEGIES:
            return str(process_instance.workflow_storage_strategy)

        configured_strategy = current_app.config.get("SPIFFWORKFLOW_BACKEND_WORKFLOW_STORAGE_STRATEGY", cls.TASK_BASED)
        if configured_strategy in cls.SUPPORTED_STRATEGIES:
            return str(configured_strategy)
        return cls.TASK_BASED

    @classmethod
    def is_blob_based_for_instance(cls, process_instance: ProcessInstanceModel) -> bool:
        return cls.strategy_for_process_instance(process_instance) == cls.BLOB_BASED

    @classmethod
    def load_workflow(cls, process_instance: ProcessInstanceModel) -> dict | None:
        record = WorkflowBlobStorageModel.query.filter_by(process_instance_id=process_instance.id).first()
        if record is None:
            return None
        return cast(dict, copy.deepcopy(record.workflow_data))

    @classmethod
    def save_workflow(cls, process_instance: ProcessInstanceModel, workflow_dict: dict) -> WorkflowBlobStorageModel:
        record = WorkflowBlobStorageModel.query.filter_by(process_instance_id=process_instance.id).first()
        if record is None:
            record = WorkflowBlobStorageModel(
                process_instance_id=process_instance.id,
                workflow_data=workflow_dict,
                serializer_version=process_instance.spiff_serializer_version,
                created_at_in_seconds=round(time.time()),
                updated_at_in_seconds=round(time.time()),
            )
        else:
            record.workflow_data = workflow_dict
            record.serializer_version = process_instance.spiff_serializer_version
            record.updated_at_in_seconds = round(time.time())

        db.session.add(record)
        return cast(WorkflowBlobStorageModel, record)

    @classmethod
    def get_task(cls, task_guid: str, process_instance: ProcessInstanceModel) -> TaskModel | SyntheticTaskModel:
        if not cls.is_blob_based_for_instance(process_instance):
            task_model: TaskModel | None = TaskModel.query.filter_by(
                guid=task_guid,
                process_instance_id=process_instance.id,
            ).first()
            if task_model is None:
                raise TaskNotFoundError(f"Cannot find task '{task_guid}' for process instance '{process_instance.id}'")
            return task_model

        from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

        processor = ProcessInstanceProcessor(
            process_instance,
            include_task_data_for_completed_tasks=True,
            include_completed_subprocesses=True,
        )
        workflow_to_guid = cls._workflow_to_guid_mapping(processor)
        spiff_task = processor.get_task_by_guid(task_guid)
        if spiff_task is None:
            raise TaskNotFoundError(f"Cannot find task '{task_guid}' for process instance '{process_instance.id}'")

        mapping_for_workflow = processor.bpmn_definition_to_task_definitions_mappings.get(spiff_task.workflow.spec.name, {})
        task_definition = mapping_for_workflow.get(spiff_task.task_spec.name)
        if task_definition is None:
            raise TaskNotFoundError(
                f"Cannot find task definition for '{spiff_task.task_spec.name}' in workflow '{spiff_task.workflow.spec.name}'"
            )

        task_properties = BpmnProcessService.serializer.to_dict(spiff_task)
        task_properties.pop("data", None)
        task_properties.pop("delta", None)
        task_data = DefaultRegistry().convert(spiff_task.data)
        python_env = cls._converted_user_defined_state(processor)
        bpmn_process = cls._task_bpmn_process(spiff_task, process_instance, processor, workflow_to_guid)

        return SyntheticTaskModel(
            guid=task_guid,
            process_instance_id=process_instance.id,
            task_definition=task_definition,
            bpmn_process=bpmn_process,
            state=TaskState.get_name(spiff_task.state),
            properties_json=task_properties,
            runtime_info=spiff_task.task_spec.task_info(spiff_task),
            task_data=task_data,
            python_env_data=python_env,
        )

    @classmethod
    def list_task_instances(cls, task_guid: str, process_instance: ProcessInstanceModel) -> list[dict]:
        if not cls.is_blob_based_for_instance(process_instance):
            return []

        task_rows = cls.list_tasks(process_instance)
        selected_task = next((task_row for task_row in task_rows if task_row["guid"] == task_guid), None)
        if selected_task is None:
            raise TaskNotFoundError(f"Cannot find task '{task_guid}' for process instance '{process_instance.id}'")

        return [
            task_row
            for task_row in task_rows
            if task_row["bpmn_identifier"] == selected_task["bpmn_identifier"]
            and task_row["bpmn_process_guid"] == selected_task["bpmn_process_guid"]
        ]

    @classmethod
    def list_tasks(cls, process_instance: ProcessInstanceModel) -> list[dict]:
        if not cls.is_blob_based_for_instance(process_instance):
            return []

        from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

        processor = ProcessInstanceProcessor(
            process_instance,
            include_task_data_for_completed_tasks=True,
            include_completed_subprocesses=True,
        )
        workflow_to_guid = cls._workflow_to_guid_mapping(processor)

        rows: list[dict] = []
        for spiff_task in processor.bpmn_process_instance.get_tasks(state=TaskState.ANY_MASK):
            mapping_for_workflow = processor.bpmn_definition_to_task_definitions_mappings.get(spiff_task.workflow.spec.name, {})
            task_definition = mapping_for_workflow.get(spiff_task.task_spec.name)
            process_definition = mapping_for_workflow.get("bpmn_process_definition")
            if task_definition is None or process_definition is None:
                continue

            task_properties = BpmnProcessService.serializer.to_dict(spiff_task)
            task_properties.pop("data", None)
            task_properties.pop("delta", None)

            state_name = TaskState.get_name(spiff_task.state)
            if state_name in ["LIKELY", "MAYBE"]:
                continue

            rows.append(
                {
                    "bpmn_process_definition_identifier": process_definition.bpmn_identifier,
                    "bpmn_process_definition_name": process_definition.bpmn_name,
                    "bpmn_process_guid": workflow_to_guid.get(id(spiff_task.workflow)),
                    "bpmn_identifier": task_definition.bpmn_identifier,
                    "bpmn_name": task_definition.bpmn_name,
                    "typename": task_definition.typename,
                    "task_definition_properties_json": task_definition.properties_json,
                    "guid": str(spiff_task.id),
                    "state": state_name,
                    "end_in_seconds": spiff_task.last_state_change if spiff_task.has_state(TaskState.FINISHED_MASK) else None,
                    "start_in_seconds": spiff_task.last_state_change,
                    "runtime_info": spiff_task.task_spec.task_info(spiff_task),
                    "properties_json": task_properties,
                }
            )
        return rows

    @classmethod
    def parent_subprocess_task_guids_for_task(cls, task_guid: str, process_instance: ProcessInstanceModel) -> list[str]:
        if not cls.is_blob_based_for_instance(process_instance):
            return []

        from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

        processor = ProcessInstanceProcessor(
            process_instance,
            include_task_data_for_completed_tasks=True,
            include_completed_subprocesses=True,
        )
        spiff_task = processor.get_task_by_guid(task_guid)
        if spiff_task is None:
            raise TaskNotFoundError(f"Cannot find task '{task_guid}' for process instance '{process_instance.id}'")

        parent_guids: list[str] = []
        seen: set[str] = set()
        parent_task_id = spiff_task.workflow.parent_task_id
        while parent_task_id is not None:
            parent_guid = str(parent_task_id)
            if parent_guid in seen:
                break
            seen.add(parent_guid)
            parent_guids.append(parent_guid)

            parent_task = processor.bpmn_process_instance.get_task_from_id(UUID(parent_guid))
            if parent_task is None:
                break
            parent_task_id = parent_task.workflow.parent_task_id
        return parent_guids

    @classmethod
    def _workflow_to_guid_mapping(cls, processor: Any) -> dict[int, str | None]:
        workflow_to_guid: dict[int, str | None] = {
            id(workflow): str(guid) for guid, workflow in processor.bpmn_process_instance.subprocesses.items()
        }
        workflow_to_guid[id(processor.bpmn_process_instance)] = None
        return workflow_to_guid

    @classmethod
    def _task_bpmn_process(
        cls,
        spiff_task: Any,
        process_instance: ProcessInstanceModel,
        processor: Any,
        workflow_to_guid: dict[int, str | None],
    ) -> BpmnProcessModel | None:
        workflow_guid = workflow_to_guid.get(id(spiff_task.workflow))
        if workflow_guid is None:
            return cast(BpmnProcessModel | None, process_instance.bpmn_process)
        bpmn_process = cast(BpmnProcessModel | None, processor.bpmn_subprocess_mapping.get(workflow_guid))
        if bpmn_process is not None:
            return bpmn_process
        return cast(BpmnProcessModel | None, BpmnProcessModel.query.filter_by(guid=workflow_guid).first())

    @classmethod
    def _converted_user_defined_state(cls, processor: Any) -> dict:
        converted = DefaultRegistry().convert(processor._script_engine.environment.user_defined_state())
        if isinstance(converted, dict):
            return converted
        return {}

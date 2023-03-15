import json
from hashlib import sha256
from typing import Optional
from typing import Tuple
from typing import TypedDict

from flask import current_app
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskStateNames
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from uuid import UUID

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401


class JsonDataDict(TypedDict):
    hash: str
    data: dict


class TaskService:
    @classmethod
    def insert_or_update_json_data_records(
        cls, json_data_hash_to_json_data_dict_mapping: dict[str, JsonDataDict]
    ) -> None:
        list_of_dicts = [*json_data_hash_to_json_data_dict_mapping.values()]
        if len(list_of_dicts) > 0:
            on_duplicate_key_stmt = None
            if current_app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"] == "mysql":
                insert_stmt = mysql_insert(JsonDataModel).values(list_of_dicts)
                on_duplicate_key_stmt = insert_stmt.on_duplicate_key_update(
                    data=insert_stmt.inserted.data, status="U"
                )
            else:
                insert_stmt = postgres_insert(JsonDataModel).values(list_of_dicts)
                on_duplicate_key_stmt = insert_stmt.on_conflict_do_nothing(
                    index_elements=["hash"]
                )
            db.session.execute(on_duplicate_key_stmt)

    @classmethod
    def update_task_model(
        cls,
        task_model: TaskModel,
        spiff_task: SpiffTask,
        serializer: BpmnWorkflowSerializer,
    ) -> Optional[JsonDataDict]:
        """Updates properties_json and data on given task_model.

        This will NOT update start_in_seconds or end_in_seconds.
        It also returns the relating json_data object so they can be imported later.
        """
        new_properties_json = serializer.task_to_dict(spiff_task)
        spiff_task_data = new_properties_json.pop("data")
        task_model.properties_json = new_properties_json
        task_model.state = TaskStateNames[new_properties_json["state"]]
        json_data_dict = cls._update_task_data_on_task_model(
            task_model, spiff_task_data
        )
        return json_data_dict

    @classmethod
    def find_or_create_task_model_from_spiff_task(
        cls,
        spiff_task: SpiffTask,
        process_instance: ProcessInstanceModel,
        serializer: BpmnWorkflowSerializer,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> Tuple[
        Optional[BpmnProcessModel],
        TaskModel,
        dict[str, TaskModel],
        dict[str, JsonDataDict],
    ]:
        spiff_task_guid = str(spiff_task.id)
        task_model: Optional[TaskModel] = TaskModel.query.filter_by(
            guid=spiff_task_guid
        ).first()
        bpmn_process = None
        new_task_models: dict[str, TaskModel] = {}
        new_json_data_dicts: dict[str, JsonDataDict] = {}
        if task_model is None:
            bpmn_process, new_task_models, new_json_data_dicts = cls.task_bpmn_process(
                spiff_task, process_instance, serializer, bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings
            )
            task_model = TaskModel.query.filter_by(guid=spiff_task_guid).first()
            if task_model is None:
                task_definition = bpmn_definition_to_task_definitions_mappings[spiff_task.workflow.spec.name][spiff_task.task_spec.name]
                task_model = TaskModel(
                    guid=spiff_task_guid, bpmn_process_id=bpmn_process.id, process_instance_id=process_instance.id, task_definition_id=task_definition.id
                )
        return (bpmn_process, task_model, new_task_models, new_json_data_dicts)

    @classmethod
    def task_subprocess(
        cls, spiff_task: SpiffTask
    ) -> Tuple[Optional[str], Optional[BpmnWorkflow]]:
        top_level_workflow = spiff_task.workflow._get_outermost_workflow()
        my_wf = spiff_task.workflow  # This is the workflow the spiff_task is part of
        my_sp = None
        my_sp_id = None
        if my_wf != top_level_workflow:
            # All the subprocesses are at the top level, so you can just compare them
            for sp_id, sp in top_level_workflow.subprocesses.items():
                if sp == my_wf:
                    my_sp = sp
                    my_sp_id = sp_id
                    break
        return (str(my_sp_id), my_sp)

    @classmethod
    def task_bpmn_process(
        cls,
        spiff_task: SpiffTask,
        process_instance: ProcessInstanceModel,
        serializer: BpmnWorkflowSerializer,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> Tuple[BpmnProcessModel, dict[str, TaskModel], dict[str, JsonDataDict]]:
        subprocess_guid, subprocess = cls.task_subprocess(spiff_task)
        bpmn_process: Optional[BpmnProcessModel] = None
        new_task_models: dict[str, TaskModel] = {}
        new_json_data_dicts: dict[str, JsonDataDict] = {}
        if subprocess is None:
            bpmn_process = process_instance.bpmn_process
            # This is the top level workflow, which has no guid
            # check for bpmn_process_id because mypy doesn't realize bpmn_process can be None
            if process_instance.bpmn_process_id is None:
                spiff_workflow = spiff_task.workflow._get_outermost_workflow()
                bpmn_process, new_task_models, new_json_data_dicts = (
                    cls.add_bpmn_process(
                        bpmn_process_dict=serializer.workflow_to_dict(
                            spiff_workflow
                        ),
                        process_instance=process_instance,
                        bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
                        spiff_workflow=spiff_workflow,
                    )
                )
        else:
            bpmn_process = BpmnProcessModel.query.filter_by(
                guid=subprocess_guid
            ).first()
            if bpmn_process is None:
                spiff_workflow = spiff_task.workflow
                bpmn_process, new_task_models, new_json_data_dicts = (
                    cls.add_bpmn_process(
                        bpmn_process_dict=serializer.workflow_to_dict(subprocess),
                        process_instance=process_instance,
                        bpmn_process_parent=process_instance.bpmn_process,
                        bpmn_process_guid=subprocess_guid,
                        bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
                        spiff_workflow=spiff_workflow,

                    )
                )
        return (bpmn_process, new_task_models, new_json_data_dicts)

    @classmethod
    def add_bpmn_process(
        cls,
        bpmn_process_dict: dict,
        process_instance: ProcessInstanceModel,
        bpmn_definition_to_task_definitions_mappings: dict,
        spiff_workflow: BpmnWorkflow,
        bpmn_process_parent: Optional[BpmnProcessModel] = None,
        bpmn_process_guid: Optional[str] = None,
    ) -> Tuple[BpmnProcessModel, dict[str, TaskModel], dict[str, JsonDataDict]]:
        """This creates and adds a bpmn_process to the Db session.

        It will also add tasks and relating json_data entries if the bpmn_process is new.
        It returns tasks and json data records in dictionaries to be added to the session later.
        """
        tasks = bpmn_process_dict.pop("tasks")
        bpmn_process_data_dict = bpmn_process_dict.pop("data")

        new_task_models = {}
        new_json_data_dicts: dict[str, JsonDataDict] = {}

        bpmn_process = None
        if bpmn_process_parent is not None:
            bpmn_process = BpmnProcessModel.query.filter_by(
                parent_process_id=bpmn_process_parent.id, guid=bpmn_process_guid
            ).first()
        elif process_instance.bpmn_process_id is not None:
            bpmn_process = process_instance.bpmn_process

        bpmn_process_is_new = False
        if bpmn_process is None:
            bpmn_process_is_new = True
            bpmn_process = BpmnProcessModel(guid=bpmn_process_guid)
        for task_id, task_properties in tasks.items():
            if task_properties['task_spec'] == 'Start':
                bpmn_process_dict['root'] = task_id

        bpmn_process.properties_json = bpmn_process_dict

        bpmn_process_data_json = json.dumps(bpmn_process_data_dict, sort_keys=True)
        bpmn_process_data_hash = sha256(
            bpmn_process_data_json.encode("utf8")
        ).hexdigest()
        if bpmn_process.json_data_hash != bpmn_process_data_hash:
            new_json_data_dicts[bpmn_process_data_hash] = {
                "hash": bpmn_process_data_hash,
                "data": bpmn_process_data_dict,
            }
            bpmn_process.json_data_hash = bpmn_process_data_hash

        if bpmn_process_parent is None:
            process_instance.bpmn_process = bpmn_process
        elif bpmn_process.parent_process_id is None:
            bpmn_process.parent_process_id = bpmn_process_parent.id

        # Since we bulk insert tasks later we need to add the bpmn_process to the session
        # to ensure we have an id.
        db.session.add(bpmn_process)

        if bpmn_process_is_new:
            for task_id, task_properties in tasks.items():
                if task_properties['task_spec'] == 'Root':
                    continue
                if task_properties['task_spec'] == 'Start':
                    task_properties['parent'] = None
                    process_dict = bpmn_process.properties_json
                    process_dict['root'] = task_id
                    bpmn_process.properties_json = process_dict
                    db.session.add(bpmn_process)
                task_data_dict = task_properties.pop("data")
                state_int = task_properties["state"]

                task_model = TaskModel.query.filter_by(guid=task_id).first()
                if task_model is None:
                    spiff_task = spiff_workflow.get_task(UUID(task_id))
                    task_model = cls._create_task(bpmn_process, process_instance, spiff_task, bpmn_definition_to_task_definitions_mappings)
                task_model.state = TaskStateNames[state_int]
                task_model.properties_json = task_properties

                json_data_dict = TaskService._update_task_data_on_task_model(
                    task_model, task_data_dict
                )
                new_task_models[task_model.guid] = task_model
                if json_data_dict is not None:
                    new_json_data_dicts[json_data_dict["hash"]] = json_data_dict

        return (bpmn_process, new_task_models, new_json_data_dicts)

    @classmethod
    def _update_task_data_on_task_model(
        cls, task_model: TaskModel, task_data_dict: dict
    ) -> Optional[JsonDataDict]:
        task_data_json = json.dumps(task_data_dict, sort_keys=True)
        task_data_hash: str = sha256(task_data_json.encode("utf8")).hexdigest()
        json_data_dict: Optional[JsonDataDict] = None
        if task_model.json_data_hash != task_data_hash:
            json_data_dict = {"hash": task_data_hash, "data": task_data_dict}
            task_model.json_data_hash = task_data_hash
        return json_data_dict

    @classmethod
    def _create_task(cls, bpmn_process: BpmnProcessModel, process_instance: ProcessInstanceModel, spiff_task: SpiffTask, bpmn_definition_to_task_definitions_mappings: dict) -> TaskModel:
        
        task_definition = bpmn_definition_to_task_definitions_mappings[spiff_task.workflow.spec.name][spiff_task.task_spec.name]
        task_model = TaskModel(
            guid=str(spiff_task.id), bpmn_process_id=bpmn_process.id, process_instance_id=process_instance.id, task_definition_id=task_definition.id
        )
        return task_model

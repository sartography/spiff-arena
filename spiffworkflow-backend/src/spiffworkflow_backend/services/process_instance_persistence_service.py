import copy

from flask import current_app
from SpiffWorkflow.bpmn.script_engine import PythonScriptEngine  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.process_instance_script_engine import CustomBpmnScriptEngine
from spiffworkflow_backend.services.task_service import StartAndEndTimes
from spiffworkflow_backend.services.task_service import TaskService


class ProcessInstancePersistenceService:
    _default_script_engine = CustomBpmnScriptEngine()

    @classmethod
    def persist_bpmn_process_dict(
        cls,
        bpmn_process_dict: dict,
        bpmn_definition_to_task_definitions_mappings: dict,
        process_instance_model: ProcessInstanceModel,
        store_process_instance_events: bool = True,
        bpmn_process_instance: BpmnWorkflow | None = None,
    ) -> None:
        # NOTE: the first add_bpmn_process_definitions is to save the objects to the database and the second
        # is to load them so we can get the db id's.
        # We could potentially do this at save time by recreating the mappings var after getting the new id.
        process_instance_model.bpmn_process_definition = BpmnProcessService.add_bpmn_process_definitions(
            bpmn_process_dict,
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
        )
        BpmnProcessService.save_to_database(
            bpmn_definition_to_task_definitions_mappings,
            bpmn_process_definition_parent=process_instance_model.bpmn_process_definition,
        )
        bpmn_definition_to_task_definitions_mappings = {}
        process_instance_model.bpmn_process_definition = BpmnProcessService.add_bpmn_process_definitions(
            bpmn_process_dict,
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
        )

        if bpmn_process_instance is None:
            bpmn_process_instance = cls.initialize_bpmn_process_instance(bpmn_process_dict)

        task_model_mapping, bpmn_subprocess_mapping = cls.get_db_mappings_from_bpmn_process_dict(bpmn_process_dict)

        task_service = TaskService(
            process_instance=process_instance_model,
            serializer=BpmnProcessService.serializer,
            bpmn_definition_to_task_definitions_mappings=bpmn_definition_to_task_definitions_mappings,
            force_update_definitions=True,
            task_model_mapping=task_model_mapping,
            bpmn_subprocess_mapping=bpmn_subprocess_mapping,
        )

        for spiff_task in bpmn_process_instance.get_tasks():
            start_and_end_times: StartAndEndTimes | None = None
            if spiff_task.has_state(TaskState.COMPLETED | TaskState.ERROR):
                start_and_end_times = {
                    "start_in_seconds": spiff_task.last_state_change,
                    "end_in_seconds": spiff_task.last_state_change,
                }
            task_service.update_task_model_with_spiff_task(
                spiff_task, store_process_instance_events=store_process_instance_events, start_and_end_times=start_and_end_times
            )
        task_service.save_objects_to_database()
        db.session.commit()

    @classmethod
    def initialize_bpmn_process_instance(cls, bpmn_process_dict: dict) -> BpmnWorkflow:
        process_copy = copy.deepcopy(bpmn_process_dict)
        bpmn_process_instance = BpmnProcessService.serializer.from_dict(process_copy)
        bpmn_process_instance.script_engine = cls._default_script_engine
        return bpmn_process_instance

    @classmethod
    def get_db_mappings_from_bpmn_process_dict(
        cls, bpmn_process_dict: dict
    ) -> tuple[dict[str, TaskModel], dict[str, BpmnProcessModel]]:
        task_guids = set(bpmn_process_dict["tasks"].keys())
        bpmn_process_guids = set()
        for subproc_guid, subproc_dict in bpmn_process_dict["subprocesses"].items():
            task_guids.update(subproc_dict["tasks"].keys())
            bpmn_process_guids.add(subproc_guid)
        task_models = TaskModel.query.filter(TaskModel.guid.in_(task_guids)).all()  # type: ignore
        bpmn_process_models = BpmnProcessModel.query.filter(BpmnProcessModel.guid.in_(bpmn_process_guids)).all()  # type: ignore
        task_model_mapping = {t.guid: t for t in task_models}
        bpmn_subprocess_mapping = {b.guid: b for b in bpmn_process_models}
        return (task_model_mapping, bpmn_subprocess_mapping)

    @classmethod
    def get_bpmn_process_instance_from_process_model(cls, process_model_identifier: str) -> BpmnWorkflow:
        (bpmn_process_spec, subprocesses) = BpmnProcessService.get_process_model_and_subprocesses(
            process_model_identifier,
        )
        bpmn_process_instance = BpmnProcessService.get_bpmn_process_instance_from_workflow_spec(bpmn_process_spec, subprocesses)
        cls.set_script_engine(bpmn_process_instance)
        return bpmn_process_instance

    @staticmethod
    def set_script_engine(bpmn_process_instance: BpmnWorkflow, script_engine: PythonScriptEngine | None = None) -> None:
        script_engine_to_use = script_engine or ProcessInstancePersistenceService._default_script_engine
        script_engine_to_use.environment.restore_state(bpmn_process_instance)
        bpmn_process_instance.script_engine = script_engine_to_use

    @classmethod
    def get_bpmn_process_dict(
        cls,
        bpmn_process: BpmnProcessModel,
        task_model_mapping: dict[str, TaskModel],
        get_tasks: bool = False,
        include_task_data_for_completed_tasks: bool = False,
    ) -> dict:
        json_data = JsonDataModel.query.filter_by(hash=bpmn_process.json_data_hash).first()
        bpmn_process_dict = {"data": json_data.data, "tasks": {}}
        bpmn_process_dict.update(bpmn_process.properties_json)
        if get_tasks:
            tasks = TaskModel.query.filter_by(bpmn_process_id=bpmn_process.id).all()
            cls.get_tasks_dict(
                tasks,
                bpmn_process_dict,
                include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                task_model_mapping=task_model_mapping,
            )
        return bpmn_process_dict

    @classmethod
    def get_tasks_dict(
        cls,
        tasks: list[TaskModel],
        spiff_bpmn_process_dict: dict,
        task_model_mapping: dict[str, TaskModel],
        bpmn_subprocess_id_to_guid_mappings: dict | None = None,
        include_task_data_for_completed_tasks: bool = False,
    ) -> None:
        json_data_hashes = set()
        states_to_exclude_from_rehydration: list[str] = []
        if not include_task_data_for_completed_tasks:
            # load CANCELLED task data for Gateways since they are marked as CANCELLED
            # and we need the task data from their parents
            states_to_exclude_from_rehydration = ["COMPLETED", "ERROR"]

        task_list_by_hash = {t.guid: t for t in tasks}
        task_guids_to_add = set()
        for task in tasks:
            parent_guid = task.parent_guid()
            if task.state not in states_to_exclude_from_rehydration:
                json_data_hashes.add(task.json_data_hash)
                task_guids_to_add.add(task.guid)

                # load parent task data to avoid certain issues that can arise from parallel branches
                if (
                    parent_guid in task_list_by_hash
                    and task_list_by_hash[parent_guid].state in states_to_exclude_from_rehydration
                ):
                    json_data_hashes.add(task_list_by_hash[parent_guid].json_data_hash)
                    task_guids_to_add.add(parent_guid)
            elif (
                parent_guid in task_list_by_hash
                and "instance_map" in (task_list_by_hash[parent_guid].runtime_info or {})
                and task_list_by_hash[parent_guid].state not in states_to_exclude_from_rehydration
            ):
                # make sure we add task data for multi-instance tasks as well
                json_data_hashes.add(task.json_data_hash)
                task_guids_to_add.add(task.guid)

        json_data_records = JsonDataModel.query.filter(JsonDataModel.hash.in_(json_data_hashes)).all()  # type: ignore
        json_data_mappings = {}
        for json_data_record in json_data_records:
            json_data_mappings[json_data_record.hash] = json_data_record.data
        for task in tasks:
            tasks_dict = spiff_bpmn_process_dict["tasks"]
            if bpmn_subprocess_id_to_guid_mappings:
                bpmn_subprocess_guid = bpmn_subprocess_id_to_guid_mappings[task.bpmn_process_id]
                tasks_dict = spiff_bpmn_process_dict["subprocesses"][bpmn_subprocess_guid]["tasks"]
            tasks_dict[task.guid] = task.properties_json
            task_data = {}
            if task.guid in task_guids_to_add:
                task_data = json_data_mappings[task.json_data_hash]
            tasks_dict[task.guid]["data"] = task_data
            task_model_mapping[task.guid] = task

    @classmethod
    def get_full_bpmn_process_dict(
        cls,
        bpmn_definition_to_task_definitions_mappings: dict,
        bpmn_subprocess_mapping: dict[str, BpmnProcessModel],
        task_model_mapping: dict[str, TaskModel],
        spiff_serializer_version: str | None = None,
        bpmn_process_definition: BpmnProcessDefinitionModel | None = None,
        bpmn_process: BpmnProcessModel | None = None,
        bpmn_process_definition_id: int | None = None,
        include_task_data_for_completed_tasks: bool = False,
        include_completed_subprocesses: bool = False,
    ) -> dict:
        if bpmn_process_definition_id is None:
            return {}

        spiff_bpmn_process_dict: dict = {
            "serializer_version": spiff_serializer_version,
            "spec": {},
            "subprocess_specs": {},
            "subprocesses": {},
        }

        if bpmn_process_definition is not None:
            spiff_bpmn_process_dict["spec"] = BpmnProcessService.get_definition_dict_for_bpmn_process_definition(
                bpmn_process_definition,
                bpmn_definition_to_task_definitions_mappings,
            )
            BpmnProcessService.set_definition_dict_for_bpmn_subprocess_definitions(
                bpmn_process_definition,
                spiff_bpmn_process_dict,
                bpmn_definition_to_task_definitions_mappings,
            )

            if bpmn_process is not None:
                single_bpmn_process_dict = cls.get_bpmn_process_dict(
                    bpmn_process,
                    get_tasks=True,
                    include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                    task_model_mapping=task_model_mapping,
                )
                spiff_bpmn_process_dict.update(single_bpmn_process_dict)

                bpmn_subprocesses_query = BpmnProcessModel.query.filter_by(top_level_process_id=bpmn_process.id)
                if not include_completed_subprocesses:
                    bpmn_subprocesses_query = bpmn_subprocesses_query.join(
                        TaskModel, TaskModel.guid == BpmnProcessModel.guid
                    ).filter(
                        TaskModel.state.not_in(["COMPLETED", "ERROR", "CANCELLED"])  # type: ignore
                    )
                bpmn_subprocesses = bpmn_subprocesses_query.all()
                bpmn_subprocess_id_to_guid_mappings = {}
                for bpmn_subprocess in bpmn_subprocesses:
                    subprocess_identifier = bpmn_subprocess.bpmn_process_definition.bpmn_identifier
                    if subprocess_identifier not in spiff_bpmn_process_dict["subprocess_specs"]:
                        current_app.logger.info(f"Deferring subprocess spec: '{subprocess_identifier}'")
                        continue
                    bpmn_subprocess_id_to_guid_mappings[bpmn_subprocess.id] = bpmn_subprocess.guid
                    single_bpmn_process_dict = cls.get_bpmn_process_dict(bpmn_subprocess, task_model_mapping=task_model_mapping)
                    spiff_bpmn_process_dict["subprocesses"][bpmn_subprocess.guid] = single_bpmn_process_dict
                    bpmn_subprocess_mapping[bpmn_subprocess.guid] = bpmn_subprocess

                tasks = TaskModel.query.filter(
                    TaskModel.bpmn_process_id.in_(bpmn_subprocess_id_to_guid_mappings.keys())  # type: ignore
                ).all()
                cls.get_tasks_dict(
                    tasks,
                    spiff_bpmn_process_dict,
                    bpmn_subprocess_id_to_guid_mappings=bpmn_subprocess_id_to_guid_mappings,
                    include_task_data_for_completed_tasks=include_task_data_for_completed_tasks,
                    task_model_mapping=task_model_mapping,
                )

        return spiff_bpmn_process_dict

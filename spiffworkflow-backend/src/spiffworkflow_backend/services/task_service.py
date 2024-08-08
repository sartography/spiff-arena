import copy
import json
import time
from hashlib import sha256
from typing import TypedDict
from uuid import UUID

from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import WorkflowException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore
from sqlalchemy import and_
from sqlalchemy import asc

from spiffworkflow_backend.exceptions.error import TaskMismatchError
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process import BpmnProcessNotFoundError
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.json_data import JsonDataDict
from spiffworkflow_backend.models.json_data import JsonDataModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.reference_cache import ReferenceNotFoundError
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task import TaskNotFoundError
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.models.task_draft_data import TaskDraftDataModel
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService


class StartAndEndTimes(TypedDict):
    start_in_seconds: float | None
    end_in_seconds: float | None


class TaskModelError(Exception):
    """Copied from SpiffWorkflow.exceptions.WorkflowTaskException.

    Reimplements the exception from SpiffWorkflow to not require a spiff_task.
    """

    def __init__(
        self,
        error_msg: str,
        task_model: TaskModel,
        exception: Exception | None = None,
        line_number: int | None = None,
        offset: int | None = None,
        error_line: str | None = None,
    ):
        self.task_model = task_model
        self.line_number = line_number
        self.offset = offset
        self.error_line = error_line
        self.notes: list[str] = []

        if exception:
            self.error_type = exception.__class__.__name__
        else:
            self.error_type = "unknown"

        if isinstance(exception, SyntaxError) and not line_number:
            self.line_number = exception.lineno
            self.offset = exception.offset
        elif isinstance(exception, NameError):
            self.add_note(WorkflowException.did_you_mean_from_name_error(exception, list(task_model.get_data().keys())))

        # If encountered in a sub-workflow, this traces back up the stack,
        # so we can tell how we got to this particular task, no matter how
        # deeply nested in sub-workflows it is.  Takes the form of:
        # task-description (file-name)
        self.task_trace = self.get_task_trace(task_model)

    def add_note(self, note: str) -> None:
        self.notes.append(note)

    def __str__(self) -> str:
        """Add notes to the error message."""
        return super().__str__() + ". " + ". ".join(self.notes)

    @classmethod
    def get_task_trace(cls, task_model: TaskModel) -> list[str]:
        task_definition = task_model.task_definition
        task_bpmn_name = TaskService.get_name_for_display(task_definition)
        bpmn_process = task_model.bpmn_process
        spec_reference_filename = TaskService.get_spec_filename_from_bpmn_process(bpmn_process)

        task_trace = [f"{task_bpmn_name} ({spec_reference_filename})"]
        while bpmn_process.guid is not None:
            caller_task_model = TaskModel.query.filter_by(guid=bpmn_process.guid).first()
            bpmn_process = BpmnProcessModel.query.filter_by(id=bpmn_process.direct_parent_process_id).first()
            spec_reference_filename = TaskService.get_spec_filename_from_bpmn_process(bpmn_process)
            task_trace.append(
                f"{TaskService.get_name_for_display(caller_task_model.task_definition)} ({spec_reference_filename})"
            )
        return task_trace


class TaskService:
    def __init__(
        self,
        process_instance: ProcessInstanceModel,
        serializer: BpmnWorkflowSerializer,
        bpmn_definition_to_task_definitions_mappings: dict,
        run_started_at: float | None = None,
        force_update_definitions: bool = False,
        task_model_mapping: dict[str, TaskModel] | None = None,
        bpmn_subprocess_mapping: dict[str, BpmnProcessModel] | None = None,
    ) -> None:
        self.process_instance = process_instance
        self.bpmn_definition_to_task_definitions_mappings = bpmn_definition_to_task_definitions_mappings
        self.serializer = serializer
        self.task_model_mapping = task_model_mapping or {}
        self.bpmn_subprocess_mapping = bpmn_subprocess_mapping or {}

        self.bpmn_subprocess_id_mapping: dict[int, BpmnProcessModel] = {}
        for _, bs in self.bpmn_subprocess_mapping.items():
            self.bpmn_subprocess_id_mapping[bs.id] = bs
        if self.process_instance.bpmn_process_id is not None:
            self.bpmn_subprocess_id_mapping[self.process_instance.bpmn_process_id] = self.process_instance.bpmn_process

        # this updates the definition ids for both tasks and bpmn_processes when they are updated
        # in case definitions were changed for the same instances.
        # this is currently only used when importing a process instance from bpmn json or when running data migrations.
        self.force_update_definitions = force_update_definitions

        self.bpmn_processes: dict[str, BpmnProcessModel] = {}
        self.task_models: dict[str, TaskModel] = {}
        self.json_data_dicts: dict[str, JsonDataDict] = {}
        self.process_instance_events: dict[str, ProcessInstanceEventModel] = {}

        self.run_started_at: float | None = run_started_at

    def save_objects_to_database(self, save_process_instance_events: bool = True) -> None:
        db.session.bulk_save_objects(self.bpmn_processes.values())
        db.session.bulk_save_objects(self.task_models.values())
        if save_process_instance_events:
            db.session.bulk_save_objects(self.process_instance_events.values())
        JsonDataModel.insert_or_update_json_data_records(self.json_data_dicts)

    def get_guid_to_db_object_mappings(self) -> tuple[dict[str, TaskModel], dict[str, BpmnProcessModel]]:
        return (self.task_model_mapping, self.bpmn_subprocess_mapping)

    def process_parents_and_children_and_save_to_database(
        self,
        spiff_task: SpiffTask,
    ) -> None:
        self.process_spiff_task_children(spiff_task)
        self.process_spiff_task_parent_subprocess_tasks(spiff_task)
        self.save_objects_to_database()

    def process_spiff_task_children(
        self,
        spiff_task: SpiffTask,
    ) -> None:
        for child_spiff_task in spiff_task.children:
            if child_spiff_task.has_state(TaskState.PREDICTED_MASK):
                self.__class__.remove_spiff_task_from_parent(child_spiff_task, self.task_models)
                continue
            self.update_task_model_with_spiff_task(
                spiff_task=child_spiff_task,
            )
            self.process_spiff_task_children(
                spiff_task=child_spiff_task,
            )

    def process_spiff_task_parent_subprocess_tasks(
        self,
        spiff_task: SpiffTask,
    ) -> None:
        """Find the parent subprocess of a given spiff_task and update its data.

        This will also process that subprocess task's children and will recurse upwards
        to process its parent subprocesses as well.
        """
        (parent_subprocess_guid, _parent_subprocess) = self.__class__._task_subprocess(spiff_task)
        if parent_subprocess_guid is not None:
            spiff_task_of_parent_subprocess = spiff_task.workflow.top_workflow.get_task_from_id(UUID(parent_subprocess_guid))

            if spiff_task_of_parent_subprocess is not None:
                self.update_task_model_with_spiff_task(
                    spiff_task=spiff_task_of_parent_subprocess,
                )
                self.process_spiff_task_children(
                    spiff_task=spiff_task_of_parent_subprocess,
                )
                self.process_spiff_task_parent_subprocess_tasks(
                    spiff_task=spiff_task_of_parent_subprocess,
                )

    def update_task_model_with_spiff_task(
        self,
        spiff_task: SpiffTask,
        start_and_end_times: StartAndEndTimes | None = None,
        store_process_instance_events: bool = True,
    ) -> TaskModel:
        new_bpmn_process = None
        if str(spiff_task.id) in self.task_models:
            task_model = self.task_models[str(spiff_task.id)]
        else:
            (
                new_bpmn_process,
                task_model,
            ) = self.find_or_create_task_model_from_spiff_task(
                spiff_task,
            )

        # we are not sure why task_model.bpmn_process can be None while task_model.bpmn_process_id actually has a valid value
        bpmn_process = new_bpmn_process or task_model.bpmn_process or self.bpmn_subprocess_id_mapping[task_model.bpmn_process_id]

        self.update_task_model(task_model, spiff_task)
        bpmn_process_json_data = self.update_task_data_on_bpmn_process(bpmn_process, bpmn_process_instance=spiff_task.workflow)
        if bpmn_process_json_data is not None:
            self.json_data_dicts[bpmn_process_json_data["hash"]] = bpmn_process_json_data
        self.task_models[task_model.guid] = task_model

        if start_and_end_times:
            task_model.start_in_seconds = start_and_end_times["start_in_seconds"]
            task_model.end_in_seconds = start_and_end_times["end_in_seconds"]

        # let failed tasks raise and we will log the event then.
        # avoid creating events for the same state transition multiple times to avoid multiple cancelled events
        if (
            store_process_instance_events
            and task_model.state in ["COMPLETED", "CANCELLED"]
            and (self.run_started_at is None or spiff_task.last_state_change >= self.run_started_at)
        ):
            event_type = ProcessInstanceEventType.task_completed.value
            if task_model.state == "CANCELLED":
                event_type = ProcessInstanceEventType.task_cancelled.value

            timestamp = task_model.end_in_seconds or task_model.start_in_seconds or time.time()
            (
                process_instance_event,
                _process_instance_error_detail,
            ) = ProcessInstanceTmpService.add_event_to_process_instance(
                self.process_instance,
                event_type,
                task_guid=task_model.guid,
                timestamp=timestamp,
                add_to_db_session=False,
            )
            self.process_instance_events[task_model.guid] = process_instance_event

        if self.force_update_definitions is True:
            task_definition = self.bpmn_definition_to_task_definitions_mappings[spiff_task.workflow.spec.name][
                spiff_task.task_spec.name
            ]
            task_model.task_definition_id = task_definition.id

        self.update_bpmn_process(spiff_task.workflow, bpmn_process)
        return task_model

    def update_bpmn_process(
        self,
        spiff_workflow: BpmnWorkflow,
        bpmn_process: BpmnProcessModel,
    ) -> None:
        new_properties_json = copy.copy(bpmn_process.properties_json)
        new_properties_json["last_task"] = str(spiff_workflow.last_task.id) if spiff_workflow.last_task else None
        new_properties_json["success"] = spiff_workflow.success
        bpmn_process.properties_json = new_properties_json

        bpmn_process_json_data = self.update_task_data_on_bpmn_process(bpmn_process, bpmn_process_instance=spiff_workflow)
        if bpmn_process_json_data is not None:
            self.json_data_dicts[bpmn_process_json_data["hash"]] = bpmn_process_json_data

        self.bpmn_processes[bpmn_process.guid or "top_level"] = bpmn_process

        if spiff_workflow.parent_task_id and bpmn_process.direct_parent_process_id:
            direct_parent_bpmn_process = self.bpmn_subprocess_id_mapping[bpmn_process.direct_parent_process_id]
            self.update_bpmn_process(spiff_workflow.parent_workflow, direct_parent_bpmn_process)

        if self.force_update_definitions is True:
            bpmn_process_definition = self.bpmn_definition_to_task_definitions_mappings[spiff_workflow.spec.name][
                "bpmn_process_definition"
            ]
            bpmn_process.bpmn_process_definition_id = bpmn_process_definition.id

    def update_task_model(
        self,
        task_model: TaskModel,
        spiff_task: SpiffTask,
    ) -> None:
        """Updates properties_json and data on given task_model.

        This will NOT update start_in_seconds or end_in_seconds.
        It also returns the relating json_data object so they can be imported later.
        """
        if str(spiff_task.id) != task_model.guid:
            raise TaskMismatchError(
                f"Given spiff task ({spiff_task.task_spec.bpmn_id} - {spiff_task.id}) and task ({task_model.guid}) must match"
            )

        new_properties_json = self.serializer.to_dict(spiff_task)

        if new_properties_json["task_spec"] == "Start":
            new_properties_json["parent"] = None
        spiff_task_data = new_properties_json.pop("data")
        python_env_data_dict = self.__class__._get_python_env_data_dict_from_spiff_task(spiff_task, self.serializer)
        task_model.properties_json = new_properties_json
        task_model.state = TaskState.get_name(new_properties_json["state"])
        json_data_dict = self.__class__.update_json_data_on_db_model_and_return_dict_if_updated(
            task_model, spiff_task_data, "json_data_hash"
        )
        python_env_dict = self.__class__.update_json_data_on_db_model_and_return_dict_if_updated(
            task_model, python_env_data_dict, "python_env_data_hash"
        )
        if json_data_dict is not None:
            self.json_data_dicts[json_data_dict["hash"]] = json_data_dict
        if python_env_dict is not None:
            self.json_data_dicts[python_env_dict["hash"]] = python_env_dict
        task_model.runtime_info = spiff_task.task_spec.task_info(spiff_task)

    def find_or_create_task_model_from_spiff_task(
        self,
        spiff_task: SpiffTask,
    ) -> tuple[BpmnProcessModel | None, TaskModel]:
        spiff_task_guid = str(spiff_task.id)
        task_model: TaskModel | None = TaskModel.query.filter_by(guid=spiff_task_guid).first()
        bpmn_process = None
        if task_model is None:
            bpmn_process = self.task_bpmn_process(spiff_task)
            task_definition = self.bpmn_definition_to_task_definitions_mappings[spiff_task.workflow.spec.name][
                spiff_task.task_spec.name
            ]
            task_model = TaskModel(
                guid=spiff_task_guid,
                bpmn_process_id=bpmn_process.id,
                process_instance_id=self.process_instance.id,
                task_definition_id=task_definition.id,
            )

        return (bpmn_process, task_model)

    def task_bpmn_process(
        self,
        spiff_task: SpiffTask,
    ) -> BpmnProcessModel:
        subprocess_guid, spiff_subprocess = self.__class__._task_subprocess(spiff_task)
        bpmn_process: BpmnProcessModel | None = None
        if spiff_subprocess is None:
            bpmn_process = self.process_instance.bpmn_process
            # This is the top level workflow, which has no guid
            # check for bpmn_process_id because mypy doesn't realize bpmn_process can be None
            if self.process_instance.bpmn_process_id is None:
                spiff_workflow = spiff_task.workflow.top_workflow
                bpmn_process = self.add_bpmn_process(
                    bpmn_process_dict=self.serializer.to_dict(spiff_workflow),
                    spiff_workflow=spiff_workflow,
                )
        else:
            bpmn_process = None
            if subprocess_guid is not None:
                bpmn_process = self.bpmn_subprocess_mapping.get(subprocess_guid)
            if bpmn_process is None:
                spiff_workflow = spiff_task.workflow
                bpmn_process = self.add_bpmn_process(
                    bpmn_process_dict=self.serializer.to_dict(spiff_subprocess),
                    top_level_process=self.process_instance.bpmn_process,
                    bpmn_process_guid=subprocess_guid,
                    spiff_workflow=spiff_workflow,
                )
        return bpmn_process

    def add_bpmn_process(
        self,
        bpmn_process_dict: dict,
        spiff_workflow: BpmnWorkflow,
        top_level_process: BpmnProcessModel | None = None,
        bpmn_process_guid: str | None = None,
    ) -> BpmnProcessModel:
        """This creates and adds a bpmn_process to the Db session.

        It will also add tasks and relating json_data entries if the bpmn_process is new.
        It returns tasks and json data records in dictionaries to be added to the session later.
        """
        tasks = bpmn_process_dict.pop("tasks")
        bpmn_process_data_dict = bpmn_process_dict.pop("data")

        if "subprocesses" in bpmn_process_dict:
            bpmn_process_dict.pop("subprocesses")
        if "spec" in bpmn_process_dict:
            bpmn_process_dict.pop("spec")
        if "subprocess_specs" in bpmn_process_dict:
            bpmn_process_dict.pop("subprocess_specs")

        bpmn_process = None
        if top_level_process is not None and bpmn_process_guid is not None:
            bpmn_process = self.bpmn_subprocess_mapping.get(bpmn_process_guid)
        elif self.process_instance.bpmn_process_id is not None:
            bpmn_process = self.process_instance.bpmn_process

        bpmn_process_is_new = False
        if bpmn_process is None:
            bpmn_process_is_new = True
            bpmn_process = BpmnProcessModel(guid=bpmn_process_guid)

            bpmn_process_definition = self.bpmn_definition_to_task_definitions_mappings[spiff_workflow.spec.name][
                "bpmn_process_definition"
            ]
            bpmn_process.bpmn_process_definition = bpmn_process_definition

            if top_level_process is not None:
                subprocesses = spiff_workflow.top_workflow.subprocesses
                direct_bpmn_process_parent: BpmnProcessModel | None = top_level_process

                # BpmnWorkflows do not know their own guid so we have to cycle through subprocesses to find the guid that matches
                # calling list(subprocesses) to make a copy of the keys so we can change subprocesses while iterating
                # changing subprocesses happens when running parallel tests
                # for reasons we do not understand. https://stackoverflow.com/a/11941855/6090676
                for subprocess_guid in list(subprocesses):
                    subprocess = subprocesses[subprocess_guid]
                    if subprocess == spiff_workflow.parent_workflow:
                        direct_bpmn_process_parent = self.bpmn_subprocess_mapping.get(str(subprocess_guid))
                        if direct_bpmn_process_parent is None:
                            raise BpmnProcessNotFoundError(
                                f"Could not find bpmn process with guid: {str(subprocess_guid)} "
                                f"while searching for direct parent process of {bpmn_process_guid}."
                            )

                if direct_bpmn_process_parent is None:
                    raise BpmnProcessNotFoundError(f"Could not find a direct bpmn process parent for guid: {bpmn_process_guid}")

                bpmn_process.direct_parent_process_id = direct_bpmn_process_parent.id

        bpmn_process.properties_json = bpmn_process_dict

        bpmn_process_json_data = self.update_task_data_on_bpmn_process(
            bpmn_process, bpmn_process_data_dict=bpmn_process_data_dict
        )
        if bpmn_process_json_data is not None:
            self.json_data_dicts[bpmn_process_json_data["hash"]] = bpmn_process_json_data

        if top_level_process is None:
            self.process_instance.bpmn_process = bpmn_process
        elif bpmn_process.top_level_process_id is None:
            bpmn_process.top_level_process_id = top_level_process.id

        # Since we bulk insert tasks later we need to add the bpmn_process to the session
        # to ensure we have an id.
        db.session.add(bpmn_process)

        if bpmn_process_is_new:
            self.add_tasks_to_bpmn_process(
                tasks=tasks,
                spiff_workflow=spiff_workflow,
                bpmn_process=bpmn_process,
            )
            if bpmn_process.guid is not None:
                self.bpmn_subprocess_mapping[bpmn_process.guid] = bpmn_process
            self.bpmn_subprocess_id_mapping[bpmn_process.id] = bpmn_process

        return bpmn_process

    def add_tasks_to_bpmn_process(
        self,
        tasks: dict,
        spiff_workflow: BpmnWorkflow,
        bpmn_process: BpmnProcessModel,
    ) -> None:
        for task_id, _task_properties in tasks.items():
            # we are going to avoid saving likely and maybe tasks to the db.
            # that means we need to remove them from their parents' lists of children as well.
            spiff_task = spiff_workflow.get_task_from_id(UUID(task_id))
            if spiff_task.has_state(TaskState.PREDICTED_MASK):
                self.__class__.remove_spiff_task_from_parent(spiff_task, self.task_models)
                continue
            task_model = TaskModel.query.filter_by(guid=task_id).first()
            if task_model is None:
                task_model = self.__class__._create_task(
                    bpmn_process,
                    self.process_instance,
                    spiff_task,
                    self.bpmn_definition_to_task_definitions_mappings,
                )
            self.update_task_model(task_model, spiff_task)
            self.task_models[task_model.guid] = task_model

    def update_all_tasks_from_spiff_tasks(
        self,
        spiff_tasks: list[SpiffTask],
        deleted_spiff_tasks: list[SpiffTask],
        start_time: float,
        to_task_guid: str | None = None,
    ) -> None:
        """Update given spiff tasks in the database and remove deleted tasks."""
        # Remove all the deleted/pruned tasks from the database.
        deleted_task_guids = [str(t.id) for t in deleted_spiff_tasks]
        tasks_to_clear = TaskModel.query.filter(TaskModel.guid.in_(deleted_task_guids)).all()  # type: ignore

        human_task_guids_to_clear = deleted_task_guids

        # ensure we clear out any human tasks that were associated with this guid in case it was a human task
        if to_task_guid is not None:
            human_task_guids_to_clear.append(to_task_guid)
        human_tasks_to_clear = HumanTaskModel.query.filter(
            HumanTaskModel.task_id.in_(human_task_guids_to_clear)  # type: ignore
        ).all()

        # delete human tasks first to avoid potential conflicts when deleting tasks.
        # otherwise sqlalchemy returns several warnings.
        for task in human_tasks_to_clear + tasks_to_clear:
            db.session.delete(task)

        bpmn_processes_to_delete = (
            BpmnProcessModel.query.filter(BpmnProcessModel.guid.in_(deleted_task_guids))  # type: ignore
            .order_by(BpmnProcessModel.id.desc())  # type: ignore
            .all()
        )
        for bpmn_process in bpmn_processes_to_delete:
            db.session.delete(bpmn_process)

        # Note: Can't restrict this to definite, because some things are updated and are now CANCELLED
        # and other things may have been COMPLETED and are now MAYBE
        spiff_tasks_updated = {}
        for spiff_task in spiff_tasks:
            if spiff_task.last_state_change > start_time:
                spiff_tasks_updated[str(spiff_task.id)] = spiff_task
        for _id, spiff_task in spiff_tasks_updated.items():
            self.update_task_model_with_spiff_task(spiff_task)

        self.save_objects_to_database()

    @classmethod
    def remove_spiff_task_from_parent(cls, spiff_task: SpiffTask, task_models: dict[str, TaskModel]) -> None:
        """Removes the given spiff task from its parent and then updates the task_models dict with the changes."""
        spiff_task_parent_guid = str(spiff_task.parent.id)
        spiff_task_guid = str(spiff_task.id)
        if spiff_task_parent_guid in task_models:
            parent_task_model = task_models[spiff_task_parent_guid]
            if spiff_task_guid in parent_task_model.properties_json["children"]:
                new_parent_properties_json = copy.copy(parent_task_model.properties_json)
                new_parent_properties_json["children"].remove(spiff_task_guid)
                parent_task_model.properties_json = new_parent_properties_json
                task_models[spiff_task_parent_guid] = parent_task_model

    def update_task_data_on_bpmn_process(
        self,
        bpmn_process: BpmnProcessModel,
        bpmn_process_data_dict: dict | None = None,
        bpmn_process_instance: BpmnWorkflow | None = None,
    ) -> JsonDataDict | None:
        data_dict_to_use = bpmn_process_data_dict
        if bpmn_process_instance is not None:
            data_dict_to_use = self.serializer.to_dict(bpmn_process_instance.data)
        if data_dict_to_use is None:
            data_dict_to_use = {}
        bpmn_process_data_json = json.dumps(data_dict_to_use, sort_keys=True)
        bpmn_process_data_hash: str = sha256(bpmn_process_data_json.encode("utf8")).hexdigest()
        json_data_dict: JsonDataDict | None = None
        if bpmn_process.json_data_hash != bpmn_process_data_hash:
            json_data_dict = {"hash": bpmn_process_data_hash, "data": data_dict_to_use}
            bpmn_process.json_data_hash = bpmn_process_data_hash
        return json_data_dict

    @classmethod
    def update_json_data_on_db_model_and_return_dict_if_updated(
        cls, db_model: SpiffworkflowBaseDBModel, task_data_dict: dict, task_model_data_column: str
    ) -> JsonDataDict | None:
        json_data_dict = JsonDataModel.json_data_dict_from_dict(task_data_dict)
        if getattr(db_model, task_model_data_column) != json_data_dict["hash"]:
            setattr(db_model, task_model_data_column, json_data_dict["hash"])
            return json_data_dict
        return None

    @classmethod
    def bpmn_process_and_descendants(cls, bpmn_processes: list[BpmnProcessModel]) -> list[BpmnProcessModel]:
        bpmn_process_ids = [p.id for p in bpmn_processes]
        direct_children = BpmnProcessModel.query.filter(
            BpmnProcessModel.direct_parent_process_id.in_(bpmn_process_ids)  # type: ignore
        ).all()
        direct_children = (
            BpmnProcessModel.query.join(TaskModel, TaskModel.guid == BpmnProcessModel.guid)
            .join(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
            .filter(
                and_(
                    TaskDefinitionModel.typename == "SubWorkflowTask",
                    TaskModel.bpmn_process_id.in_(bpmn_process_ids),  # type: ignore
                )
            )
            .all()
        )
        if len(direct_children) > 0:
            return bpmn_processes + cls.bpmn_process_and_descendants(direct_children)
        return bpmn_processes

    @classmethod
    def task_models_of_parent_bpmn_processes(
        cls, task_model: TaskModel, stop_on_first_call_activity: bool | None = False
    ) -> tuple[list[BpmnProcessModel], list[TaskModel]]:
        """Returns the list of task models that are associated with the parent bpmn process.

        Example: TopLevelProcess has SubprocessTaskA which has CallActivityTaskA which has ScriptTaskA.
        SubprocessTaskA corresponds to SpiffSubprocess1.
        CallActivityTaskA corresponds to SpiffSubprocess2.
        Using ScriptTaskA this will return:
            (
                [TopLevelProcess, SpiffSubprocess1, SpiffSubprocess2],
                [SubprocessTaskA, CallActivityTaskA]
            )

        If stop_on_first_call_activity it will stop when it reaches the first task model with a type of 'CallActivity'.
        This will change the return value in the example to:
            (
                [SpiffSubprocess2],
                [CallActivityTaskA]
            )
        """
        bpmn_process = task_model.bpmn_process
        task_models: list[TaskModel] = []
        bpmn_processes: list[BpmnProcessModel] = [bpmn_process]
        if bpmn_process.guid is not None:
            parent_task_model = TaskModel.query.filter_by(guid=bpmn_process.guid).first()
            task_models.append(parent_task_model)
            if not stop_on_first_call_activity or parent_task_model.task_definition.typename != "CallActivity":
                if parent_task_model is not None:
                    b, t = cls.task_models_of_parent_bpmn_processes(
                        parent_task_model, stop_on_first_call_activity=stop_on_first_call_activity
                    )
                    # order matters here. since we are traversing backwards (from child to parent) then
                    # b and t should be the parents of whatever is in bpmn_processes and task_models.
                    return (b + bpmn_processes, t + task_models)
        return (bpmn_processes, task_models)

    @classmethod
    def full_bpmn_process_path(cls, bpmn_process: BpmnProcessModel, definition_column: str = "bpmn_identifier") -> list[str]:
        """Returns a list of bpmn process identifiers pointing the given bpmn_process."""
        bpmn_process_identifiers: list[str] = []
        if bpmn_process.guid:
            task_model = TaskModel.query.filter_by(guid=bpmn_process.guid).first()
            if task_model is None:
                raise TaskNotFoundError(f"Cannot find the corresponding task for the bpmn process with guid {bpmn_process.guid}.")
            (
                parent_bpmn_processes,
                _task_models_of_parent_bpmn_processes,
            ) = TaskService.task_models_of_parent_bpmn_processes(task_model)
            for parent_bpmn_process in parent_bpmn_processes:
                bpmn_process_identifiers.append(getattr(parent_bpmn_process.bpmn_process_definition, definition_column))
        bpmn_process_identifiers.append(getattr(bpmn_process.bpmn_process_definition, definition_column))
        return bpmn_process_identifiers

    @classmethod
    def task_draft_data_from_task_model(
        cls, task_model: TaskModel, create_if_not_exists: bool = False
    ) -> TaskDraftDataModel | None:
        full_bpmn_process_id_path = cls.full_bpmn_process_path(task_model.bpmn_process, "id")
        task_definition_id_path = f"{':'.join(map(str, full_bpmn_process_id_path))}:{task_model.task_definition_id}"
        task_draft_data: TaskDraftDataModel | None = TaskDraftDataModel.query.filter_by(
            process_instance_id=task_model.process_instance_id, task_definition_id_path=task_definition_id_path
        ).first()
        if task_draft_data is None and create_if_not_exists:
            task_draft_data = TaskDraftDataModel(
                process_instance_id=task_model.process_instance_id, task_definition_id_path=task_definition_id_path
            )
        return task_draft_data

    @classmethod
    def get_task_type_from_spiff_task(cls, spiff_task: SpiffTask) -> str:
        # wrap in str so mypy doesn't lose its mind
        return str(spiff_task.task_spec.__class__.__name__)

    @classmethod
    def is_main_process_end_event(cls, spiff_task: SpiffTask) -> bool:
        return cls.get_task_type_from_spiff_task(spiff_task) == "EndEvent" and spiff_task.workflow.parent_workflow is None

    @classmethod
    def bpmn_process_for_called_activity_or_top_level_process(cls, task_model: TaskModel) -> BpmnProcessModel:
        """Returns either the bpmn process for the call activity calling the process or the top level bpmn process.

        For example, process_modelA has processA which has a call activity that calls processB which is inside of process_modelB.
        processB has subprocessA which has taskA. Using taskA this method should return processB and then that can be used with
        the spec reference cache to find process_modelB.
        """
        (bpmn_processes, _task_models) = TaskService.task_models_of_parent_bpmn_processes(
            task_model, stop_on_first_call_activity=True
        )
        return bpmn_processes[0]

    @classmethod
    def reset_task_model_dict(
        cls,
        task_model: dict,
        state: str,
    ) -> None:
        task_model["state"] = state
        task_model["start_in_seconds"] = None
        task_model["end_in_seconds"] = None

    @classmethod
    def get_extensions_from_task_model(cls, task_model: TaskModel) -> dict:
        task_definition = task_model.task_definition
        extensions: dict = (
            task_definition.properties_json["extensions"] if "extensions" in task_definition.properties_json else {}
        )
        return extensions

    @classmethod
    def get_ready_signals_with_button_labels(cls, process_instance_id: int, associated_task_guid: str) -> list[dict]:
        waiting_tasks: list[TaskModel] = TaskModel.query.filter_by(state="WAITING", process_instance_id=process_instance_id).all()
        result = []
        for task_model in waiting_tasks:
            task_definition = task_model.task_definition
            extensions: dict = (
                task_definition.properties_json["extensions"] if "extensions" in task_definition.properties_json else {}
            )
            event_definition: dict = (
                task_definition.properties_json["event_definition"]
                if "event_definition" in task_definition.properties_json
                else {}
            )
            if "signalButtonLabel" in extensions and "name" in event_definition:
                parent_task_model = task_model.parent_task_model()
                if (
                    parent_task_model
                    and "children" in parent_task_model.properties_json
                    and associated_task_guid in parent_task_model.properties_json["children"]
                ):
                    result.append({"event": event_definition, "label": extensions["signalButtonLabel"]})
        return result

    @classmethod
    def get_spec_filename_from_bpmn_process(cls, bpmn_process: BpmnProcessModel) -> str | None:
        """Just return the filename if the bpmn process is found in spec reference cache."""
        try:
            filename: str | None = cls.get_spec_reference_from_bpmn_process(bpmn_process).file_name
            return filename
        except ReferenceNotFoundError:
            return None

    @classmethod
    def get_spec_reference_from_bpmn_process(cls, bpmn_process: BpmnProcessModel) -> ReferenceCacheModel:
        """Get the bpmn file for a given task model.

        This involves several queries so avoid calling in a tight loop.
        """
        bpmn_process_definition = bpmn_process.bpmn_process_definition
        spec_reference: ReferenceCacheModel | None = (
            ReferenceCacheModel.basic_query()
            .filter_by(identifier=bpmn_process_definition.bpmn_identifier, type="process")
            .first()
        )
        if spec_reference is None:
            raise ReferenceNotFoundError(
                f"Could not find given process identifier in the cache: {bpmn_process_definition.bpmn_identifier}"
            )
        return spec_reference

    @classmethod
    def get_name_for_display(cls, entity: TaskDefinitionModel | BpmnProcessDefinitionModel) -> str:
        return entity.bpmn_name or entity.bpmn_identifier

    @classmethod
    def next_human_task_for_user(cls, process_instance_id: int, user_id: int) -> HumanTaskModel | None:
        next_human_task: HumanTaskModel | None = (
            HumanTaskModel.query.filter_by(process_instance_id=process_instance_id, completed=False)
            .order_by(asc(HumanTaskModel.id))  # type: ignore
            .join(HumanTaskUserModel)
            .filter_by(user_id=user_id)
            .first()
        )
        return next_human_task

    @classmethod
    def _task_subprocess(cls, spiff_task: SpiffTask) -> tuple[str | None, BpmnWorkflow | None]:
        top_level_workflow = spiff_task.workflow.top_workflow
        my_wf = spiff_task.workflow  # This is the workflow the spiff_task is part of
        my_sp = None
        my_sp_id = None
        if my_wf != top_level_workflow:
            # All the subprocesses are at the top level, so you can just compare them
            for sp_id, sp in top_level_workflow.subprocesses.items():
                if sp == my_wf:
                    my_sp = sp
                    my_sp_id = str(sp_id)
                    break
        return (my_sp_id, my_sp)

    @classmethod
    def _create_task(
        cls,
        bpmn_process: BpmnProcessModel,
        process_instance: ProcessInstanceModel,
        spiff_task: SpiffTask,
        bpmn_definition_to_task_definitions_mappings: dict,
    ) -> TaskModel:
        task_definition = bpmn_definition_to_task_definitions_mappings[spiff_task.workflow.spec.name][spiff_task.task_spec.name]
        task_model = TaskModel(
            guid=str(spiff_task.id),
            bpmn_process_id=bpmn_process.id,
            process_instance_id=process_instance.id,
            task_definition_id=task_definition.id,
        )
        return task_model

    @classmethod
    def _get_python_env_data_dict_from_spiff_task(cls, spiff_task: SpiffTask, serializer: BpmnWorkflowSerializer) -> dict:
        user_defined_state = spiff_task.workflow.script_engine.environment.user_defined_state()
        # this helps to convert items like datetime objects to be json serializable
        converted_data: dict = serializer.registry.convert(user_defined_state)
        return converted_data

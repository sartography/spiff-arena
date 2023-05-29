"""Process_instance_service."""
import base64
import hashlib
import time
from datetime import datetime
from datetime import timezone
from typing import Any
from typing import Dict
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from urllib.parse import unquote

import sentry_sdk
from flask import current_app
from flask import g
from SpiffWorkflow.bpmn.specs.control import _BoundaryEventParent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions import TimerEventDefinition  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend import db
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceApi
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_file_data import (
    ProcessInstanceFileDataModel,
)
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import HumanTaskNotFoundError
from spiffworkflow_backend.services.authorization_service import UserDoesNotHaveAccessToTaskError
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_queue_service import (
    ProcessInstanceIsAlreadyLockedError,
)
from spiffworkflow_backend.services.process_instance_queue_service import (
    ProcessInstanceQueueService,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.workflow_service import WorkflowService
from spiffworkflow_backend.specs.start_event import StartConfiguration


class ProcessInstanceService:
    """ProcessInstanceService."""

    FILE_DATA_DIGEST_PREFIX = "spifffiledatadigest+"
    TASK_STATE_LOCKED = "locked"

    @staticmethod
    def next_start_event_configuration(process_instance_model: ProcessInstanceModel) -> StartConfiguration:
        try:
            processor = ProcessInstanceProcessor(process_instance_model)
            start_configuration = WorkflowService.next_start_event_configuration(
                processor.bpmn_process_instance, datetime.now(timezone.utc)
            )
        except Exception:
            start_configuration = None

        if start_configuration is None:
            start_configuration = (0, 0, 0)

        return start_configuration

    @classmethod
    def create_process_instance(
        cls,
        process_model: ProcessModelInfo,
        user: UserModel,
    ) -> Tuple[ProcessInstanceModel, StartConfiguration]:
        """Get_process_instance_from_spec."""
        db.session.commit()
        try:
            current_git_revision = GitService.get_current_revision()
        except GitCommandError:
            current_git_revision = ""
        process_instance_model = ProcessInstanceModel(
            status=ProcessInstanceStatus.not_started.value,
            process_initiator_id=user.id,
            process_model_identifier=process_model.id,
            process_model_display_name=process_model.display_name,
            start_in_seconds=round(time.time()),
            bpmn_version_control_type="git",
            bpmn_version_control_identifier=current_git_revision,
        )
        db.session.add(process_instance_model)
        db.session.commit()
        cycles, delay_in_seconds, duration = cls.next_start_event_configuration(process_instance_model)
        run_at_in_seconds = round(time.time()) + delay_in_seconds
        ProcessInstanceQueueService.enqueue_new_process_instance(process_instance_model, run_at_in_seconds)
        return (process_instance_model, (cycles, delay_in_seconds, duration))

    @classmethod
    def create_process_instance_from_process_model_identifier(
        cls,
        process_model_identifier: str,
        user: UserModel,
    ) -> ProcessInstanceModel:
        """Create_process_instance_from_process_model_identifier."""
        process_model = ProcessModelService.get_process_model(process_model_identifier)
        process_instance_model, _ = cls.create_process_instance(process_model, user)
        return process_instance_model

    @classmethod
    def waiting_event_can_be_skipped(cls, waiting_event: Dict[str, Any], now_in_utc: datetime) -> bool:
        #
        # over time this function can gain more knowledge of different event types,
        # for now we are just handling Duration Timer events.
        #
        # example: {'event_type': 'Duration Timer', 'name': None, 'value': '2023-04-27T20:15:10.626656+00:00'}
        #
        spiff_event_type = waiting_event.get("event_type")
        if spiff_event_type == "DurationTimerEventDefinition":
            event_value = waiting_event.get("value")
            if event_value is not None:
                event_datetime = TimerEventDefinition.get_datetime(event_value)
                return event_datetime > now_in_utc  # type: ignore
        return False

    @classmethod
    def all_waiting_events_can_be_skipped(cls, waiting_events: List[Dict[str, Any]]) -> bool:
        for waiting_event in waiting_events:
            if not cls.waiting_event_can_be_skipped(waiting_event, datetime.now(timezone.utc)):
                return False
        return True

    @classmethod
    def ready_user_task_has_associated_timer(cls, processor: ProcessInstanceProcessor) -> bool:
        for ready_user_task in processor.bpmn_process_instance.get_ready_user_tasks():
            if isinstance(ready_user_task.parent.task_spec, _BoundaryEventParent):
                return True
        return False

    @classmethod
    def can_optimistically_skip(cls, processor: ProcessInstanceProcessor, status_value: str) -> bool:
        if not current_app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_ALLOW_OPTIMISTIC_CHECKS"]:
            return False

        if processor.process_instance_model.status != status_value:
            return True

        if status_value == "user_input_required" and cls.ready_user_task_has_associated_timer(processor):
            return cls.all_waiting_events_can_be_skipped(processor.bpmn_process_instance.waiting_events())

        return False

    @classmethod
    def do_waiting(cls, status_value: str) -> None:
        """Do_waiting."""
        run_at_in_seconds_threshold = round(time.time())
        process_instance_ids_to_check = ProcessInstanceQueueService.peek_many(
            status_value, run_at_in_seconds_threshold
        )
        if len(process_instance_ids_to_check) == 0:
            return

        records = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id.in_(process_instance_ids_to_check))  # type: ignore
            .all()
        )
        execution_strategy_name = current_app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND"]
        for process_instance in records:
            current_app.logger.info(f"Processing process_instance {process_instance.id}")
            try:
                cls.run_process_instance_with_processor(
                    process_instance, status_value=status_value, execution_strategy_name=execution_strategy_name
                )
            except ProcessInstanceIsAlreadyLockedError:
                continue
            except Exception as e:
                db.session.rollback()  # in case the above left the database with a bad transaction
                error_message = (
                    f"Error running waiting task for process_instance {process_instance.id}"
                    + f"({process_instance.process_model_identifier}). {str(e)}"
                )
                current_app.logger.error(error_message)

    @classmethod
    def run_process_instance_with_processor(
        cls,
        process_instance: ProcessInstanceModel,
        status_value: Optional[str] = None,
        execution_strategy_name: Optional[str] = None,
    ) -> Optional[ProcessInstanceProcessor]:
        processor = None
        with ProcessInstanceQueueService.dequeued(process_instance):
            processor = ProcessInstanceProcessor(process_instance)
        if status_value and cls.can_optimistically_skip(processor, status_value):
            current_app.logger.info(f"Optimistically skipped process_instance {process_instance.id}")
            return None

        db.session.refresh(process_instance)
        if status_value is None or process_instance.status == status_value:
            processor.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name)

        return processor

    @staticmethod
    def processor_to_process_instance_api(
        processor: ProcessInstanceProcessor, next_task: None = None
    ) -> ProcessInstanceApi:
        """Returns an API model representing the state of the current process_instance.

        If requested, and possible, next_task is set to the current_task.
        """
        # navigation = processor.bpmn_process_instance.get_deep_nav_list()
        # ProcessInstanceService.update_navigation(navigation, processor)
        ProcessModelService.get_process_model(processor.process_model_identifier)
        process_instance_api = ProcessInstanceApi(
            id=processor.get_process_instance_id(),
            status=processor.get_status(),
            next_task=None,
            process_model_identifier=processor.process_model_identifier,
            process_model_display_name=processor.process_model_display_name,
            updated_at_in_seconds=processor.process_instance_model.updated_at_in_seconds,
        )

        next_task_trying_again = next_task
        if not next_task:  # The Next Task can be requested to be a certain task, useful for parallel tasks.
            # This may or may not work, sometimes there is no next task to complete.
            next_task_trying_again = processor.next_task()

        if next_task_trying_again is not None:
            process_instance_api.next_task = ProcessInstanceService.spiff_task_to_api_task(
                processor, next_task_trying_again, add_docs_and_forms=True
            )

        return process_instance_api

    def get_process_instance(self, process_instance_id: int) -> Any:
        """Get_process_instance."""
        result = db.session.query(ProcessInstanceModel).filter(ProcessInstanceModel.id == process_instance_id).first()
        return result

    @staticmethod
    def get_users_assigned_to_task(processor: ProcessInstanceProcessor, spiff_task: SpiffTask) -> List[int]:
        """Get_users_assigned_to_task."""
        if processor.process_instance_model.process_initiator_id is None:
            raise ApiError.from_task(
                error_code="invalid_workflow",
                message="A process instance must have a user_id.",
                task=spiff_task,
            )

        # Workflow associated with a study - get all the users
        else:
            if not hasattr(spiff_task.task_spec, "lane") or spiff_task.task_spec.lane is None:
                return [processor.process_instance_model.process_initiator_id]

            if spiff_task.task_spec.lane not in spiff_task.data:
                return []  # No users are assignable to the task at this moment
            lane_users = spiff_task.data[spiff_task.task_spec.lane]
            if not isinstance(lane_users, list):
                lane_users = [lane_users]

            lane_uids = []
            for user in lane_users:
                if isinstance(user, dict):
                    if user.get("value"):
                        lane_uids.append(user["value"])
                    else:
                        raise ApiError.from_task(
                            error_code="task_lane_user_error",
                            message=(
                                "Spiff Task %s lane user dict must have a key called"
                                " 'value' with the user's uid in it."
                            )
                            % spiff_task.task_spec.name,
                            task=spiff_task,
                        )
                elif isinstance(user, str):
                    lane_uids.append(user)
                else:
                    raise ApiError.from_task(
                        error_code="task_lane_user_error",
                        message="Spiff Task %s lane user is not a string or dict" % spiff_task.task_spec.name,
                        task=spiff_task,
                    )

            return lane_uids

    @classmethod
    def file_data_model_for_value(
        cls,
        identifier: str,
        value: str,
        process_instance_id: int,
    ) -> Optional[ProcessInstanceFileDataModel]:
        if value.startswith("data:"):
            try:
                parts = value.split(";")
                mimetype = parts[0][5:]
                filename = unquote(parts[1].split("=")[1])
                base64_value = parts[2].split(",")[1]
                if not base64_value.startswith(cls.FILE_DATA_DIGEST_PREFIX):
                    contents = base64.b64decode(base64_value)
                    digest = hashlib.sha256(contents).hexdigest()
                    now_in_seconds = round(time.time())

                    return ProcessInstanceFileDataModel(
                        process_instance_id=process_instance_id,
                        identifier=identifier,
                        mimetype=mimetype,
                        filename=filename,
                        contents=contents,  # type: ignore
                        digest=digest,
                        updated_at_in_seconds=now_in_seconds,
                        created_at_in_seconds=now_in_seconds,
                    )
            except Exception as e:
                print(e)

        return None

    @classmethod
    def possible_file_data_values(
        cls,
        data: dict[str, Any],
    ) -> Generator[Tuple[str, str, Optional[int]], None, None]:
        for identifier, value in data.items():
            if isinstance(value, str):
                yield (identifier, value, None)
            if isinstance(value, list):
                for list_index, list_value in enumerate(value):
                    if isinstance(list_value, str):
                        yield (identifier, list_value, list_index)
                    if isinstance(list_value, dict) and len(list_value) == 1:
                        for v in list_value.values():
                            if isinstance(v, str):
                                yield (identifier, v, list_index)

    @classmethod
    def file_data_models_for_data(
        cls,
        data: dict[str, Any],
        process_instance_id: int,
    ) -> List[ProcessInstanceFileDataModel]:
        models = []

        for identifier, value, list_index in cls.possible_file_data_values(data):
            model = cls.file_data_model_for_value(identifier, value, process_instance_id)
            if model is not None:
                model.list_index = list_index
                models.append(model)

        return models

    @classmethod
    def replace_file_data_with_digest_references(
        cls,
        data: dict[str, Any],
        models: List[ProcessInstanceFileDataModel],
    ) -> None:
        for model in models:
            digest_reference = (
                f"data:{model.mimetype};name={model.filename};base64,{cls.FILE_DATA_DIGEST_PREFIX}{model.digest}"
            )
            if model.list_index is None:
                data[model.identifier] = digest_reference
            else:
                old_value = data[model.identifier][model.list_index]
                new_value: Any = digest_reference
                if isinstance(old_value, dict) and len(old_value) == 1:
                    new_value = {k: digest_reference for k in old_value.keys()}
                data[model.identifier][model.list_index] = new_value

    @classmethod
    def save_file_data_and_replace_with_digest_references(
        cls,
        data: dict[str, Any],
        process_instance_id: int,
    ) -> None:
        models = cls.file_data_models_for_data(data, process_instance_id)

        for model in models:
            db.session.add(model)
        db.session.commit()

        cls.replace_file_data_with_digest_references(data, models)

    @classmethod
    def update_form_task_data(
        cls,
        process_instance: ProcessInstanceModel,
        spiff_task: SpiffTask,
        data: dict[str, Any],
        user: UserModel,
    ) -> None:
        AuthorizationService.assert_user_can_complete_task(process_instance.id, spiff_task.task_spec.name, user)
        cls.save_file_data_and_replace_with_digest_references(
            data,
            process_instance.id,
        )
        dot_dct = cls.create_dot_dict(data)
        spiff_task.update_data(dot_dct)

    @staticmethod
    def complete_form_task(
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
        data: dict[str, Any],
        user: UserModel,
        human_task: HumanTaskModel,
    ) -> None:
        """All the things that need to happen when we complete a form.

        Abstracted here because we need to do it multiple times when completing all tasks in
        a multi-instance task.
        """
        ProcessInstanceService.update_form_task_data(processor.process_instance_model, spiff_task, data, user)
        # ProcessInstanceService.post_process_form(spiff_task)  # some properties may update the data store.
        processor.complete_task(spiff_task, human_task, user=user)

        with sentry_sdk.start_span(op="task", description="backend_do_engine_steps"):
            # maybe move this out once we have the interstitial page since this is here just so we can get the next human task
            processor.do_engine_steps(save=True)

    @staticmethod
    def create_dot_dict(data: dict) -> dict[str, Any]:
        """Create_dot_dict."""
        dot_dict: dict[str, Any] = {}
        for key, value in data.items():
            ProcessInstanceService.set_dot_value(key, value, dot_dict)
        return dot_dict

    @staticmethod
    def get_dot_value(path: str, source: dict) -> Any:
        """Get_dot_value."""
        # Given a path in dot notation, uas as 'fruit.type' tries to find that value in
        # the source, but looking deep in the dictionary.
        paths = path.split(".")  # [a,b,c]
        s = source
        index = 0
        for p in paths:
            index += 1
            if isinstance(s, dict) and p in s:
                if index == len(paths):
                    return s[p]
                else:
                    s = s[p]
        if path in source:
            return source[path]
        return None

    @staticmethod
    def set_dot_value(path: str, value: Any, target: dict) -> dict:
        """Set_dot_value."""
        # Given a path in dot notation, such as "fruit.type", and a value "apple", will
        # set the value in the target dictionary, as target["fruit"]["type"]="apple"
        destination = target
        paths = path.split(".")  # [a,b,c]
        index = 0
        for p in paths:
            index += 1
            if p not in destination:
                if index == len(paths):
                    destination[p] = value
                else:
                    destination[p] = {}
            destination = destination[p]
        return target

    @staticmethod
    def spiff_task_to_api_task(
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
        add_docs_and_forms: bool = False,
        calling_subprocess_task_id: Optional[str] = None,
    ) -> Task:
        """Spiff_task_to_api_task."""
        task_type = spiff_task.task_spec.description

        props = {}
        if hasattr(spiff_task.task_spec, "extensions"):
            for key, val in spiff_task.task_spec.extensions.items():
                props[key] = val

        if hasattr(spiff_task.task_spec, "lane"):
            lane = spiff_task.task_spec.lane
        else:
            lane = None

        # Check for a human task, and if it exists, check to see if the current user
        # can complete it.
        can_complete = False
        try:
            AuthorizationService.assert_user_can_complete_task(
                processor.process_instance_model.id, spiff_task.task_spec.name, g.user
            )
            can_complete = True
        except HumanTaskNotFoundError:
            can_complete = False
        except UserDoesNotHaveAccessToTaskError:
            can_complete = False

        if hasattr(spiff_task.task_spec, "spec"):
            call_activity_process_identifier = spiff_task.task_spec.spec
        else:
            call_activity_process_identifier = None

        parent_id = None
        if spiff_task.parent:
            parent_id = spiff_task.parent.id

        serialized_task_spec = processor.serialize_task_spec(spiff_task.task_spec)

        # Grab the last error message.
        error_message = None
        for event in processor.process_instance_model.process_instance_events:
            for detail in event.error_details:
                error_message = detail.message

        task = Task(
            spiff_task.id,
            spiff_task.task_spec.bpmn_id,
            spiff_task.task_spec.bpmn_name,
            task_type,
            spiff_task.get_state_name(),
            can_complete=can_complete,
            lane=lane,
            process_identifier=spiff_task.task_spec._wf_spec.name,
            process_instance_id=processor.process_instance_model.id,
            process_model_identifier=processor.process_model_identifier,
            process_model_display_name=processor.process_model_display_name,
            properties=props,
            parent=parent_id,
            event_definition=serialized_task_spec.get("event_definition"),
            call_activity_process_identifier=call_activity_process_identifier,
            calling_subprocess_task_id=calling_subprocess_task_id,
            error_message=error_message,
        )

        return task

"""Process_instance_service."""
import base64
import hashlib
import time
from typing import Any
from typing import Generator
from typing import List
from typing import Optional
from typing import Tuple
from urllib.parse import unquote

import sentry_sdk
from flask import current_app
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


class ProcessInstanceService:
    """ProcessInstanceService."""

    FILE_DATA_DIGEST_PREFIX = "spifffiledatadigest+"
    TASK_STATE_LOCKED = "locked"

    @classmethod
    def create_process_instance(
        cls,
        process_model: ProcessModelInfo,
        user: UserModel,
    ) -> ProcessInstanceModel:
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
        return process_instance_model

    @classmethod
    def create_process_instance_from_process_model_identifier(
        cls,
        process_model_identifier: str,
        user: UserModel,
    ) -> ProcessInstanceModel:
        """Create_process_instance_from_process_model_identifier."""
        process_model = ProcessModelService.get_process_model(process_model_identifier)
        return cls.create_process_instance(process_model, user)

    @staticmethod
    def do_waiting(status_value: str = ProcessInstanceStatus.waiting.value) -> None:
        """Do_waiting."""
        locked_process_instance_ids = ProcessInstanceQueueService.dequeue_many(
            status_value
        )
        if len(locked_process_instance_ids) == 0:
            return

        records = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id.in_(locked_process_instance_ids))  # type: ignore
            .all()
        )
        process_instance_lock_prefix = "Background"
        for process_instance in records:
            locked = False
            processor = None
            try:
                current_app.logger.info(
                    f"Processing process_instance {process_instance.id}"
                )
                processor = ProcessInstanceProcessor(process_instance)
                processor.lock_process_instance(process_instance_lock_prefix)
                locked = True
                execution_strategy_name = current_app.config[
                    "SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND"
                ]
                processor.do_engine_steps(
                    save=True, execution_strategy_name=execution_strategy_name
                )
            except ProcessInstanceIsAlreadyLockedError:
                continue
            except Exception as e:
                db.session.rollback()  # in case the above left the database with a bad transaction
                process_instance.status = ProcessInstanceStatus.error.value
                db.session.add(process_instance)
                db.session.commit()
                error_message = (
                    "Error running waiting task for process_instance"
                    f" {process_instance.id}"
                    + f"({process_instance.process_model_identifier}). {str(e)}"
                )
                current_app.logger.error(error_message)
            finally:
                if locked and processor:
                    processor.unlock_process_instance(process_instance_lock_prefix)

    @staticmethod
    def processor_to_process_instance_api(
        processor: ProcessInstanceProcessor, next_task: None = None
    ) -> ProcessInstanceApi:
        """Returns an API model representing the state of the current process_instance.

        If requested, and possible, next_task is set to the current_task.
        """
        # navigation = processor.bpmn_process_instance.get_deep_nav_list()
        # ProcessInstanceService.update_navigation(navigation, processor)
        process_model_service = ProcessModelService()
        process_model = process_model_service.get_process_model(
            processor.process_model_identifier
        )
        process_model.display_name if process_model else ""
        process_instance_api = ProcessInstanceApi(
            id=processor.get_process_instance_id(),
            status=processor.get_status(),
            next_task=None,
            process_model_identifier=processor.process_model_identifier,
            process_model_display_name=processor.process_model_display_name,
            completed_tasks=processor.process_instance_model.completed_tasks,
            updated_at_in_seconds=processor.process_instance_model.updated_at_in_seconds,
        )

        next_task_trying_again = next_task
        if (
            not next_task
        ):  # The Next Task can be requested to be a certain task, useful for parallel tasks.
            # This may or may not work, sometimes there is no next task to complete.
            next_task_trying_again = processor.next_task()

        if next_task_trying_again is not None:
            process_instance_api.next_task = (
                ProcessInstanceService.spiff_task_to_api_task(
                    processor, next_task_trying_again, add_docs_and_forms=True
                )
            )

        return process_instance_api

    def get_process_instance(self, process_instance_id: int) -> Any:
        """Get_process_instance."""
        result = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == process_instance_id)
            .first()
        )
        return result

    @staticmethod
    def get_users_assigned_to_task(
        processor: ProcessInstanceProcessor, spiff_task: SpiffTask
    ) -> List[int]:
        """Get_users_assigned_to_task."""
        if processor.process_instance_model.process_initiator_id is None:
            raise ApiError.from_task(
                error_code="invalid_workflow",
                message="A process instance must have a user_id.",
                task=spiff_task,
            )

        # Workflow associated with a study - get all the users
        else:
            if (
                not hasattr(spiff_task.task_spec, "lane")
                or spiff_task.task_spec.lane is None
            ):
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
                        message="Spiff Task %s lane user is not a string or dict"
                        % spiff_task.task_spec.name,
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

    @classmethod
    def file_data_models_for_data(
        cls,
        data: dict[str, Any],
        process_instance_id: int,
    ) -> List[ProcessInstanceFileDataModel]:
        models = []

        for identifier, value, list_index in cls.possible_file_data_values(data):
            model = cls.file_data_model_for_value(
                identifier, value, process_instance_id
            )
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
            digest_reference = f"data:{model.mimetype};name={model.filename};base64,{cls.FILE_DATA_DIGEST_PREFIX}{model.digest}"
            if model.list_index is None:
                data[model.identifier] = digest_reference
            else:
                data[model.identifier][model.list_index] = digest_reference

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
        AuthorizationService.assert_user_can_complete_spiff_task(
            processor.process_instance_model.id, spiff_task, user
        )

        ProcessInstanceService.save_file_data_and_replace_with_digest_references(
            data,
            processor.process_instance_model.id,
        )

        dot_dct = ProcessInstanceService.create_dot_dict(data)
        spiff_task.update_data(dot_dct)
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
        task_spiff_step: Optional[int] = None,
    ) -> Task:
        """Spiff_task_to_api_task."""
        task_type = spiff_task.task_spec.spec_type

        props = {}
        if hasattr(spiff_task.task_spec, "extensions"):
            for key, val in spiff_task.task_spec.extensions.items():
                props[key] = val

        if hasattr(spiff_task.task_spec, "lane"):
            lane = spiff_task.task_spec.lane
        else:
            lane = None

        if hasattr(spiff_task.task_spec, "spec"):
            call_activity_process_identifier = spiff_task.task_spec.spec
        else:
            call_activity_process_identifier = None

        parent_id = None
        if spiff_task.parent:
            parent_id = spiff_task.parent.id

        serialized_task_spec = processor.serialize_task_spec(spiff_task.task_spec)

        task = Task(
            spiff_task.id,
            spiff_task.task_spec.name,
            spiff_task.task_spec.description,
            task_type,
            spiff_task.get_state_name(),
            lane=lane,
            process_identifier=spiff_task.task_spec._wf_spec.name,
            properties=props,
            parent=parent_id,
            event_definition=serialized_task_spec.get("event_definition"),
            call_activity_process_identifier=call_activity_process_identifier,
            calling_subprocess_task_id=calling_subprocess_task_id,
            task_spiff_step=task_spiff_step,
        )

        return task

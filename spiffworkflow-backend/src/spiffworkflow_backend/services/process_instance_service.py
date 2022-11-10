"""Process_instance_service."""
import time
from typing import Any
from typing import List

from flask import current_app
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.models.process_instance import ProcessInstanceApi
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.task import MultiInstanceType
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_model_service import ProcessModelService


class ProcessInstanceService:
    """ProcessInstanceService."""

    TASK_STATE_LOCKED = "locked"

    @staticmethod
    def create_process_instance(
        process_model_identifier: str,
        user: UserModel,
    ) -> ProcessInstanceModel:
        """Get_process_instance_from_spec."""
        current_git_revision = GitService.get_current_revision()
        process_instance_model = ProcessInstanceModel(
            status=ProcessInstanceStatus.not_started.value,
            process_initiator=user,
            process_model_identifier=process_model_identifier,
            process_group_identifier="",
            start_in_seconds=round(time.time()),
            bpmn_version_control_type="git",
            bpmn_version_control_identifier=current_git_revision,
        )
        db.session.add(process_instance_model)
        db.session.commit()
        return process_instance_model

    @staticmethod
    def do_waiting() -> None:
        """Do_waiting."""
        records = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.status == ProcessInstanceStatus.waiting.value)
            .all()
        )
        for process_instance in records:
            try:
                current_app.logger.info(
                    f"Processing process_instance {process_instance.id}"
                )
                processor = ProcessInstanceProcessor(process_instance)
                processor.do_engine_steps(save=True)
            except Exception as e:
                db.session.rollback()  # in case the above left the database with a bad transaction
                process_instance.status = ProcessInstanceStatus.error.value
                db.session.add(process_instance)
                db.session.commit()
                error_message = (
                    f"Error running waiting task for process_instance {process_instance.id}"
                    + f"({process_instance.process_model_identifier}). {str(e)}"
                )
                current_app.logger.error(error_message)

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
        is_review_value = process_model.is_review if process_model else False
        title_value = process_model.display_name if process_model else ""
        process_instance_api = ProcessInstanceApi(
            id=processor.get_process_instance_id(),
            status=processor.get_status(),
            next_task=None,
            # navigation=navigation,
            process_model_identifier=processor.process_model_identifier,
            process_group_identifier="",
            # total_tasks=len(navigation),
            completed_tasks=processor.process_instance_model.completed_tasks,
            updated_at_in_seconds=processor.process_instance_model.updated_at_in_seconds,
            is_review=is_review_value,
            title=title_value,
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
                    next_task_trying_again, add_docs_and_forms=True
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
                current_user = spiff_task.data["current_user"]
                return [
                    current_user["id"],
                ]
                # return [processor.process_instance_model.process_initiator_id]

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
                            message="Spiff Task %s lane user dict must have a key called 'value' with the user's uid in it."
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

    @staticmethod
    def complete_form_task(
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
        data: dict[str, Any],
        user: UserModel,
    ) -> None:
        """All the things that need to happen when we complete a form.

        Abstracted here because we need to do it multiple times when completing all tasks in
        a multi-instance task.
        """
        AuthorizationService.assert_user_can_complete_spiff_task(
            processor, spiff_task, user
        )

        dot_dct = ProcessInstanceService.create_dot_dict(data)
        spiff_task.update_data(dot_dct)
        # ProcessInstanceService.post_process_form(spiff_task)  # some properties may update the data store.
        processor.complete_task(spiff_task)
        processor.do_engine_steps(save=True)

    @staticmethod
    def extract_form_data(latest_data: dict, task: SpiffTask) -> dict:
        """Extracts data from the latest_data that is directly related to the form that is being submitted."""
        data = {}

        if hasattr(task.task_spec, "form"):
            for field in task.task_spec.form.fields:
                if field.has_property(Task.FIELD_PROP_REPEAT):
                    group = field.get_property(Task.FIELD_PROP_REPEAT)
                    if group in latest_data:
                        data[group] = latest_data[group]
                else:
                    value = ProcessInstanceService.get_dot_value(field.id, latest_data)
                    if value is not None:
                        ProcessInstanceService.set_dot_value(field.id, value, data)
        return data

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
        spiff_task: SpiffTask, add_docs_and_forms: bool = False
    ) -> Task:
        """Spiff_task_to_api_task."""
        task_type = spiff_task.task_spec.spec_type

        info = spiff_task.task_info()
        if info["is_looping"]:
            mi_type = MultiInstanceType.looping
        elif info["is_sequential_mi"]:
            mi_type = MultiInstanceType.sequential
        elif info["is_parallel_mi"]:
            mi_type = MultiInstanceType.parallel
        else:
            mi_type = MultiInstanceType.none

        props = {}
        if hasattr(spiff_task.task_spec, "extensions"):
            for key, val in spiff_task.task_spec.extensions.items():
                props[key] = val

        if hasattr(spiff_task.task_spec, "lane"):
            lane = spiff_task.task_spec.lane
        else:
            lane = None

        parent_id = None
        if spiff_task.parent:
            parent_id = spiff_task.parent.id

        task = Task(
            spiff_task.id,
            spiff_task.task_spec.name,
            spiff_task.task_spec.description,
            task_type,
            spiff_task.get_state_name(),
            lane=lane,
            multi_instance_type=mi_type,
            multi_instance_count=info["mi_count"],
            multi_instance_index=info["mi_index"],
            process_name=spiff_task.task_spec._wf_spec.description,
            properties=props,
            parent=parent_id,
        )

        return task

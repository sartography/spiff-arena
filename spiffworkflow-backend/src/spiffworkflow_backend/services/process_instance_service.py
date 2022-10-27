"""Process_instance_service."""
import time
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from flask import current_app
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore

from spiffworkflow_backend.models.process_instance import ProcessInstanceApi
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.task import MultiInstanceType
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task_event import TaskAction
from spiffworkflow_backend.models.task_event import TaskEventModel
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
        process_group_identifier: Optional[str] = None,
    ) -> ProcessInstanceModel:
        """Get_process_instance_from_spec."""
        current_git_revision = GitService.get_current_revision()
        process_instance_model = ProcessInstanceModel(
            status=ProcessInstanceStatus.not_started.value,
            process_initiator=user,
            process_model_identifier=process_model_identifier,
            process_group_identifier=process_group_identifier,
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
                process_instance.status = ProcessInstanceStatus.erroring.value
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
            process_group_identifier=processor.process_group_identifier,
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
            previous_form_data = ProcessInstanceService.get_previously_submitted_data(
                processor.process_instance_model.id, next_task_trying_again
            )
            #            DeepMerge.merge(next_task_trying_again.data, previous_form_data)
            next_task_trying_again.data = DeepMerge.merge(
                previous_form_data, next_task_trying_again.data
            )

            process_instance_api.next_task = (
                ProcessInstanceService.spiff_task_to_api_task(
                    next_task_trying_again, add_docs_and_forms=True
                )
            )
            # TODO: Hack for now, until we decide how to implment forms
            process_instance_api.next_task.form = None

            # Update the state of the task to locked if the current user does not own the task.
            # user_uids = WorkflowService.get_users_assigned_to_task(processor, next_task)
            # if not UserService.in_list(user_uids, allow_admin_impersonate=True):
            #     workflow_api.next_task.state = WorkflowService.TASK_STATE_LOCKED

        return process_instance_api

    @staticmethod
    def get_previously_submitted_data(
        process_instance_id: int, spiff_task: SpiffTask
    ) -> Dict[Any, Any]:
        """If the user has completed this task previously, find the form data for the last submission."""
        query = (
            db.session.query(TaskEventModel)
            .filter_by(process_instance_id=process_instance_id)
            .filter_by(task_name=spiff_task.task_spec.name)
            .filter_by(action=TaskAction.COMPLETE.value)
        )

        if (
            hasattr(spiff_task, "internal_data")
            and "runtimes" in spiff_task.internal_data
        ):
            query = query.filter_by(mi_index=spiff_task.internal_data["runtimes"])

        latest_event = query.order_by(TaskEventModel.date.desc()).first()
        if latest_event:
            if latest_event.form_data is not None:
                return latest_event.form_data  # type: ignore
            else:
                missing_form_error = (
                    f"We have lost data for workflow {process_instance_id}, "
                    f"task {spiff_task.task_spec.name}, it is not in the task event model, "
                    f"and it should be."
                )
                current_app.logger.exception(
                    "missing_form_data", missing_form_error
                )
                return {}
        else:
            return {}

    def get_process_instance(self, process_instance_id: int) -> Any:
        """Get_process_instance."""
        result = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.id == process_instance_id)
            .first()
        )
        return result

    @staticmethod
    def update_task_assignments(processor: ProcessInstanceProcessor) -> None:
        """For every upcoming user task, log a task action that connects the assigned user(s) to that task.

        All existing assignment actions for this workflow are removed from the database,
        so that only the current valid actions are available. update_task_assignments
        should be called whenever progress is made on a workflow.
        """
        db.session.query(TaskEventModel).filter(
            TaskEventModel.process_instance_id == processor.process_instance_model.id
        ).filter(TaskEventModel.action == TaskAction.ASSIGNMENT.value).delete()
        db.session.commit()

        tasks = processor.get_current_user_tasks()
        for task in tasks:
            user_ids = ProcessInstanceService.get_users_assigned_to_task(
                processor, task
            )

            for user_id in user_ids:
                ProcessInstanceService().log_task_action(
                    user_id, processor, task, TaskAction.ASSIGNMENT.value
                )

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
        # Log the action before doing the engine steps, as doing so could effect the state of the task
        # the workflow could wrap around in the ngine steps, and the task could jump from being completed to
        # another state.  What we are logging here is the completion.
        ProcessInstanceService.log_task_action(
            user.id, processor, spiff_task, TaskAction.COMPLETE.value
        )
        processor.do_engine_steps(save=True)

    @staticmethod
    def log_task_action(
        user_id: int,
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
        action: str,
    ) -> None:
        """Log_task_action."""
        task = ProcessInstanceService.spiff_task_to_api_task(spiff_task)
        form_data = ProcessInstanceService.extract_form_data(
            spiff_task.data, spiff_task
        )
        multi_instance_type_value = ""
        if task.multi_instance_type:
            multi_instance_type_value = task.multi_instance_type.value

        task_event = TaskEventModel(
            # study_id=processor.workflow_model.study_id,
            user_id=user_id,
            process_instance_id=processor.process_instance_model.id,
            # workflow_spec_id=processor.workflow_model.workflow_spec_id,
            action=action,
            task_id=str(task.id),
            task_name=task.name,
            task_title=task.title,
            task_type=str(task.type),
            task_state=task.state,
            task_lane=task.lane,
            form_data=form_data,
            mi_type=multi_instance_type_value,  # Some tasks have a repeat behavior.
            mi_count=task.multi_instance_count,  # This is the number of times the task could repeat.
            mi_index=task.multi_instance_index,  # And the index of the currently repeating task.
            process_name=task.process_name,
            # date=datetime.utcnow(), <=== For future reference, NEVER do this. Let the database set the time.
        )
        db.session.add(task_event)
        db.session.commit()

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

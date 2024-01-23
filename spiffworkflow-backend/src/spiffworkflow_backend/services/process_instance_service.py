import base64
import hashlib
import time
from collections.abc import Generator
from contextlib import suppress
from datetime import datetime
from datetime import timezone
from typing import Any
from urllib.parse import unquote

import sentry_sdk
from flask import current_app
from flask import g
from SpiffWorkflow.bpmn.event import PendingBpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.control import BoundaryEventSplit  # type: ignore
from SpiffWorkflow.bpmn.specs.defaults import BoundaryEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.timer import TimerEventDefinition  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_enabled_for_process_model,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import HumanTaskAlreadyCompletedError
from spiffworkflow_backend.exceptions.error import HumanTaskNotFoundError
from spiffworkflow_backend.exceptions.error import UserDoesNotHaveAccessToTaskError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceApi
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model_cycle import ProcessModelCycleModel
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability
from spiffworkflow_backend.services.workflow_service import WorkflowService
from spiffworkflow_backend.specs.start_event import StartConfiguration

FileDataGenerator = Generator[tuple[dict | list, str | int, str], None, None]


class ProcessInstanceService:
    FILE_DATA_DIGEST_PREFIX = "spifffiledatadigest+"
    TASK_STATE_LOCKED = "locked"

    @staticmethod
    def user_has_started_instance(process_model_identifier: str) -> bool:
        started_instance = (
            db.session.query(ProcessInstanceModel)
            .filter(
                ProcessInstanceModel.process_model_identifier == process_model_identifier,
                ProcessInstanceModel.status != "not_started",
            )
            .first()
        )
        return started_instance is not None

    @staticmethod
    def times_executed_by_user(process_model_identifier: str) -> int:
        total = (
            db.session.query(ProcessInstanceModel)
            .filter(ProcessInstanceModel.process_model_identifier == process_model_identifier)
            .count()
        )
        return total

    @staticmethod
    def next_start_event_configuration(process_instance_model: ProcessInstanceModel) -> StartConfiguration:
        try:
            # this is only called from create_process_instance so no need to worry about process instance migrations
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
        start_configuration: StartConfiguration | None = None,
    ) -> tuple[ProcessInstanceModel, StartConfiguration]:
        db.session.commit()
        try:
            current_git_revision = GitService.get_current_revision()
        except GitCommandError:
            current_git_revision = None
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

        if start_configuration is None:
            start_configuration = cls.next_start_event_configuration(process_instance_model)
        _, delay_in_seconds, _ = start_configuration
        run_at_in_seconds = round(time.time()) + delay_in_seconds
        ProcessInstanceQueueService.enqueue_new_process_instance(process_instance_model, run_at_in_seconds)
        return (process_instance_model, start_configuration)

    @classmethod
    def create_process_instance_from_process_model_identifier(
        cls,
        process_model_identifier: str,
        user: UserModel,
    ) -> ProcessInstanceModel:
        process_model = ProcessModelService.get_process_model(process_model_identifier)
        process_instance_model, (cycle_count, _, duration_in_seconds) = cls.create_process_instance(process_model, user)
        cls.register_process_model_cycles(process_model_identifier, cycle_count, duration_in_seconds)
        return process_instance_model

    @classmethod
    def register_process_model_cycles(cls, process_model_identifier: str, cycle_count: int, duration_in_seconds: int) -> None:
        # clean up old cycle record if it exists. event if the given cycle_count is 0 the previous version
        # of the model could have included a cycle timer start event
        cycles = ProcessModelCycleModel.query.filter(
            ProcessModelCycleModel.process_model_identifier == process_model_identifier,
        ).all()

        for cycle in cycles:
            db.session.delete(cycle)

        db.session.commit()

        if cycle_count != 0:
            if duration_in_seconds == 0:
                raise ApiError(
                    error_code="process_model_cycle_has_0_second_duration",
                    message="Can not schedule a process model cycle with a duration in seconds of 0.",
                )

            cycle = ProcessModelCycleModel(
                process_model_identifier=process_model_identifier,
                cycle_count=cycle_count,
                duration_in_seconds=duration_in_seconds,
                current_cycle=0,
            )
            db.session.add(cycle)
            db.session.commit()

    @classmethod
    def schedule_next_process_model_cycle(cls, process_instance_model: ProcessInstanceModel) -> None:
        cycle = ProcessModelCycleModel.query.filter(
            ProcessModelCycleModel.process_model_identifier == process_instance_model.process_model_identifier
        ).first()

        if cycle is None or cycle.cycle_count == 0:
            return

        if cycle.cycle_count == -1 or cycle.current_cycle < cycle.cycle_count:
            process_model = ProcessModelService.get_process_model(process_instance_model.process_model_identifier)
            start_configuration = (cycle.cycle_count, cycle.duration_in_seconds, cycle.duration_in_seconds)
            cls.create_process_instance(process_model, process_instance_model.process_initiator, start_configuration)
            cycle.current_cycle += 1
            db.session.add(cycle)
            db.session.commit()

    @classmethod
    def waiting_event_can_be_skipped(cls, waiting_event: PendingBpmnEvent, now_in_utc: datetime) -> bool:
        #
        # over time this function can gain more knowledge of different event types,
        # for now we are just handling Duration Timer events.
        #
        # example: {'event_type': 'Duration Timer', 'name': None, 'value': '2023-04-27T20:15:10.626656+00:00'}
        #
        spiff_event_type = waiting_event.event_type
        if spiff_event_type == "DurationTimerEventDefinition":
            event_value = waiting_event.value
            if event_value is not None:
                event_datetime = TimerEventDefinition.get_datetime(event_value)
                return event_datetime > now_in_utc  # type: ignore
        return False

    @classmethod
    def all_waiting_events_can_be_skipped(cls, waiting_events: list[dict[str, Any]]) -> bool:
        for waiting_event in waiting_events:
            if not cls.waiting_event_can_be_skipped(waiting_event, datetime.now(timezone.utc)):
                return False
        return True

    @classmethod
    def ready_user_task_has_associated_timer(cls, processor: ProcessInstanceProcessor) -> bool:
        for ready_user_task in processor.bpmn_process_instance.get_tasks(state=TaskState.READY, manual=True):
            if isinstance(ready_user_task.parent.task_spec, BoundaryEventSplit):
                for boundary_event_child in ready_user_task.parent.children:
                    child_task_spec = boundary_event_child.task_spec
                    if (
                        isinstance(child_task_spec, BoundaryEvent)
                        and "Timer" in child_task_spec.event_definition.__class__.__name__
                    ):
                        return True
        return False

    @classmethod
    def can_optimistically_skip(cls, processor: ProcessInstanceProcessor, status_value: str) -> bool:
        if not current_app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_ALLOW_OPTIMISTIC_CHECKS"]:
            return False

        if processor.process_instance_model.status != status_value:
            return True

        if status_value == "user_input_required":
            if cls.ready_user_task_has_associated_timer(processor):
                return cls.all_waiting_events_can_be_skipped(processor.bpmn_process_instance.waiting_events())
            return True

        return False

    # this is only used from background processor
    @classmethod
    def do_waiting(cls, status_value: str) -> None:
        run_at_in_seconds_threshold = round(time.time())
        min_age_in_seconds = 60  # to avoid conflicts with the interstitial page, we wait 60 seconds before processing
        process_instance_ids_to_check = ProcessInstanceQueueService.peek_many(
            status_value, run_at_in_seconds_threshold, min_age_in_seconds
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
            current_app.logger.info(f"Processor {status_value}: Processing process_instance {process_instance.id}")
            try:
                cls.run_process_instance_with_processor(
                    process_instance, status_value=status_value, execution_strategy_name=execution_strategy_name
                )
            except ProcessInstanceIsAlreadyLockedError:
                continue
            except Exception as e:
                db.session.rollback()  # in case the above left the database with a bad transaction
                error_message = (
                    f"Error running {status_value} task for process_instance {process_instance.id}"
                    + f"({process_instance.process_model_identifier}). {str(e)}"
                )
                current_app.logger.error(error_message)

    @classmethod
    def run_process_instance_with_processor(
        cls,
        process_instance: ProcessInstanceModel,
        status_value: str | None = None,
        execution_strategy_name: str | None = None,
        additional_processing_identifier: str | None = None,
    ) -> tuple[ProcessInstanceProcessor | None, TaskRunnability]:
        processor = None
        task_runnability = TaskRunnability.unknown_if_ready_tasks
        with ProcessInstanceQueueService.dequeued(
            process_instance, additional_processing_identifier=additional_processing_identifier
        ):
            ProcessInstanceMigrator.run(process_instance)
            processor = ProcessInstanceProcessor(
                process_instance,
                workflow_completed_handler=cls.schedule_next_process_model_cycle,
                additional_processing_identifier=additional_processing_identifier,
            )

        # if status_value is user_input_required (we are processing instances with that status from background processor),
        # the ONLY reason we need to do anything is if the task has a timer boundary event on it that has triggered.
        # otherwise, in all cases, we should optimistically skip it.
        if status_value and cls.can_optimistically_skip(processor, status_value):
            current_app.logger.info(f"Optimistically skipped process_instance {process_instance.id}")
            return (processor, task_runnability)

        db.session.refresh(process_instance)
        if status_value is None or process_instance.status == status_value:
            task_runnability = processor.do_engine_steps(
                save=True,
                execution_strategy_name=execution_strategy_name,
            )

        return (processor, task_runnability)

    @staticmethod
    def processor_to_process_instance_api(process_instance: ProcessInstanceModel) -> ProcessInstanceApi:
        """Returns an API model representing the state of the current process_instance."""
        process_instance_api = ProcessInstanceApi(
            id=process_instance.id,
            status=process_instance.status,
            process_model_identifier=process_instance.process_model_identifier,
            process_model_display_name=process_instance.process_model_display_name,
            updated_at_in_seconds=process_instance.updated_at_in_seconds,
        )

        return process_instance_api

    def get_process_instance(self, process_instance_id: int) -> Any:
        result = db.session.query(ProcessInstanceModel).filter(ProcessInstanceModel.id == process_instance_id).first()
        return result

    @staticmethod
    def get_users_assigned_to_task(processor: ProcessInstanceProcessor, spiff_task: SpiffTask) -> list[int]:
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
                            message="Spiff Task %s lane user dict must have a key called 'value' with the user's uid in it."
                            % spiff_task.task_spec.name,
                            task=spiff_task,
                        )
                elif isinstance(user, str):
                    lane_uids.append(user)
                else:
                    raise ApiError.from_task(
                        error_code="task_lane_user_error",
                        message=f"Spiff Task {spiff_task.task_spec.name} lane user is not a string or dict",
                        task=spiff_task,
                    )

            return lane_uids

    @classmethod
    def file_data_model_for_value(
        cls,
        value: str,
        process_instance_id: int,
    ) -> ProcessInstanceFileDataModel | None:
        with suppress(Exception):
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
                    mimetype=mimetype,
                    filename=filename,
                    contents=contents,  # type: ignore
                    digest=digest,
                    updated_at_in_seconds=now_in_seconds,
                    created_at_in_seconds=now_in_seconds,
                )

        return None

    @classmethod
    def possible_file_data_values(
        cls,
        data: dict[str, Any],
    ) -> FileDataGenerator:
        def values(collection: dict | list, elem: str | int | None, value: Any) -> FileDataGenerator:
            match (collection, elem, value):
                case (dict(), None, None):
                    for k, v in collection.items():  # type: ignore
                        yield from values(collection, k, v)
                case (list(), None, None):
                    for i, v in enumerate(collection):
                        yield from values(collection, i, v)
                case (_, _, dict() | list()):
                    yield from values(value, None, None)
                case (_, _, str()) if elem is not None and value.startswith("data:"):
                    yield (collection, elem, value)

        yield from values(data, None, None)

    @classmethod
    def replace_file_data_with_digest_references(
        cls,
        data: dict[str, Any],
        process_instance_id: int,
    ) -> list[ProcessInstanceFileDataModel]:
        models = []

        for collection, elem, value in cls.possible_file_data_values(data):
            model = cls.file_data_model_for_value(value, process_instance_id)
            if model is None:
                continue
            models.append(model)
            digest_reference = f"data:{model.mimetype};name={model.filename};base64,{cls.FILE_DATA_DIGEST_PREFIX}{model.digest}"
            collection[elem] = digest_reference  # type: ignore

        return models

    @classmethod
    def save_file_data_and_replace_with_digest_references(
        cls,
        data: dict[str, Any],
        process_instance_id: int,
    ) -> None:
        models = cls.replace_file_data_with_digest_references(data, process_instance_id)

        for model in models:
            db.session.add(model)
        db.session.commit()

    @classmethod
    def update_form_task_data(
        cls,
        process_instance: ProcessInstanceModel,
        spiff_task: SpiffTask,
        data: dict[str, Any],
        user: UserModel,
    ) -> None:
        AuthorizationService.assert_user_can_complete_task(process_instance.id, str(spiff_task.id), user)
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

        if queue_enabled_for_process_model(processor.process_instance_model):
            queue_process_instance_if_appropriate(processor.process_instance_model)
        else:
            with sentry_sdk.start_span(op="task", description="backend_do_engine_steps"):
                # maybe move this out once we have the interstitial page since this is here just so we can get the next human task
                processor.do_engine_steps(save=True)

    @staticmethod
    def create_dot_dict(data: dict) -> dict[str, Any]:
        dot_dict: dict[str, Any] = {}
        for key, value in data.items():
            ProcessInstanceService.set_dot_value(key, value, dot_dict)
        return dot_dict

    @staticmethod
    def get_dot_value(path: str, source: dict) -> Any:
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
    ) -> Task:
        task_type = spiff_task.task_spec.description
        task_guid = str(spiff_task.id)

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
            AuthorizationService.assert_user_can_complete_task(processor.process_instance_model.id, task_guid, g.user)
            can_complete = True
        except HumanTaskAlreadyCompletedError:
            can_complete = False
        except HumanTaskNotFoundError:
            can_complete = False
        except UserDoesNotHaveAccessToTaskError:
            can_complete = False

        # if the current user cannot complete the task then find out who can
        assigned_user_group_identifier = None
        potential_owner_usernames = None
        if can_complete is False:
            human_task = HumanTaskModel.query.filter_by(task_id=task_guid).first()
            if human_task is not None:
                if human_task.lane_assignment_id is not None:
                    group = GroupModel.query.filter_by(id=human_task.lane_assignment_id).first()
                    if group is not None:
                        assigned_user_group_identifier = group.identifier
                elif len(human_task.potential_owners) > 0:
                    user_list = [u.email for u in human_task.potential_owners]
                    potential_owner_usernames = ",".join(user_list)

        parent_id = None
        if spiff_task.parent:
            parent_id = spiff_task.parent.id

        serialized_task_spec = processor.serialize_task_spec(spiff_task.task_spec)

        # Grab the last error message.
        error_message = None
        error_event = ProcessInstanceEventModel.query.filter_by(
            task_guid=task_guid, event_type=ProcessInstanceEventType.task_failed.value
        ).first()
        if error_event:
            error_message = error_event.error_details[-1].message

        task = Task(
            spiff_task.id,
            spiff_task.task_spec.bpmn_id,
            spiff_task.task_spec.bpmn_name,
            task_type,
            TaskState.get_name(spiff_task.state),
            can_complete=can_complete,
            lane=lane,
            process_identifier=spiff_task.task_spec._wf_spec.name,
            process_instance_id=processor.process_instance_model.id,
            process_model_identifier=processor.process_model_identifier,
            process_model_display_name=processor.process_model_display_name,
            properties=props,
            parent=parent_id,
            event_definition=serialized_task_spec.get("event_definition"),
            error_message=error_message,
            assigned_user_group_identifier=assigned_user_group_identifier,
            potential_owner_usernames=potential_owner_usernames,
        )

        return task

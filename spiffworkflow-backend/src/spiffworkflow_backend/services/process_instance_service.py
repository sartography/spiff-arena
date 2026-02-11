import base64
import copy
import hashlib
import json
import time
from collections.abc import Generator
from contextlib import suppress
from datetime import datetime
from datetime import timezone
from hashlib import sha256
from typing import Any
from urllib.parse import unquote
from uuid import UUID

import jsonschema
import sentry_sdk
from flask import current_app
from flask import g
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore
from SpiffWorkflow.bpmn.specs.control import BoundaryEventSplit  # type: ignore
from SpiffWorkflow.bpmn.specs.defaults import BoundaryEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.timer import TimerEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.util import PendingBpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.util.diff import WorkflowDiff  # type: ignore
from SpiffWorkflow.bpmn.util.diff import diff_workflow
from SpiffWorkflow.bpmn.util.diff import filter_tasks
from SpiffWorkflow.bpmn.util.diff import migrate_workflow
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.deep_merge import DeepMerge  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore
from sqlalchemy import or_

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import should_queue_process_instance
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import HumanTaskAlreadyCompletedError
from spiffworkflow_backend.exceptions.error import HumanTaskNotFoundError
from spiffworkflow_backend.exceptions.error import ProcessInstanceMigrationNotSafeError
from spiffworkflow_backend.exceptions.error import ProcessInstanceMigrationUnnecessaryError
from spiffworkflow_backend.exceptions.error import UserDoesNotHaveAccessToTaskError
from spiffworkflow_backend.helpers.spiff_enum import ProcessInstanceExecutionMode
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceApi
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.models.process_instance_migration_detail import ProcessInstanceMigrationDetailModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model_cycle import ProcessModelCycleModel
from spiffworkflow_backend.models.task import Task
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.logging_service import LoggingService
from spiffworkflow_backend.services.process_instance_processor import CustomBpmnScriptEngine
from spiffworkflow_backend.services.process_instance_processor import IdToBpmnProcessSpecMapping
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_processor import SubprocessUuidToWorkflowDiffMapping
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsNotEnqueuedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.workflow_execution_service import TaskRunnability
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError
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
        load_bpmn_process_model: bool = True,
    ) -> tuple[ProcessInstanceModel, StartConfiguration]:
        git_revision_error = None
        try:
            current_git_revision = GitService.get_current_revision()
        except GitCommandError as ex:
            git_revision_error = ex
            current_git_revision = None

        if load_bpmn_process_model:
            BpmnProcessService.persist_bpmn_process_definition(process_model.id)

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

        if git_revision_error is not None:
            message = (
                f"Failed to get the current git revision when attempting to create a process instance"
                f" ({process_instance_model.id}) for process_model: '{process_model.id}'. Error was {str(git_revision_error)}"
            )
            current_app.logger.warning(message)

        if start_configuration is None:
            start_configuration = cls.next_start_event_configuration(process_instance_model)
        _, delay_in_seconds, _ = start_configuration
        run_at_in_seconds = round(time.time()) + delay_in_seconds
        ProcessInstanceQueueService.enqueue_new_process_instance(process_instance_model, run_at_in_seconds)
        return (process_instance_model, start_configuration)

    @classmethod
    def check_process_instance_can_be_migrated(
        cls,
        process_instance: ProcessInstanceModel,
        target_bpmn_process_hash: str | None = None,
    ) -> tuple[
        ProcessInstanceProcessor, BpmnProcessSpec, IdToBpmnProcessSpecMapping, WorkflowDiff, SubprocessUuidToWorkflowDiffMapping
    ]:
        if target_bpmn_process_hash is None:
            (target_bpmn_process_spec, target_subprocess_specs) = BpmnProcessService.get_process_model_and_subprocesses(
                process_instance.process_model_identifier,
            )
            full_bpmn_spec_dict = {
                "spec": BpmnProcessService.serializer.to_dict(target_bpmn_process_spec),
                "subprocess_specs": BpmnProcessService.serializer.to_dict(target_subprocess_specs),
            }
            target_bpmn_process_hash = sha256(json.dumps(full_bpmn_spec_dict, sort_keys=True).encode("utf8")).hexdigest()
        else:
            bpmn_process_definition = BpmnProcessDefinitionModel.query.filter_by(
                full_process_model_hash=target_bpmn_process_hash
            ).first()
            full_bpmn_process_dict = ProcessInstanceProcessor._get_full_bpmn_process_dict(
                bpmn_definition_to_task_definitions_mappings={},
                spiff_serializer_version=process_instance.spiff_serializer_version,
                bpmn_process_definition=bpmn_process_definition,
                bpmn_process_definition_id=bpmn_process_definition.id,
                task_model_mapping={},
                bpmn_subprocess_mapping={},
            )
            process_copy = copy.deepcopy(full_bpmn_process_dict)
            target_bpmn_process_spec = BpmnProcessService.serializer.from_dict(process_copy["spec"])
            target_subprocess_specs = BpmnProcessService.serializer.from_dict(process_copy["subprocess_specs"])

        initial_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        if target_bpmn_process_hash == initial_bpmn_process_hash:
            raise ProcessInstanceMigrationUnnecessaryError(
                "Both target and current process model versions are the same. There is no need to migrate."
            )
        processor = ProcessInstanceProcessor(
            process_instance, include_task_data_for_completed_tasks=True, include_completed_subprocesses=True
        )

        # tasks that were in the old workflow and are in the new one as well
        top_level_bpmn_process_diff, subprocesses_diffs = diff_workflow(
            BpmnProcessService.serializer.registry,
            processor.bpmn_process_instance,
            target_bpmn_process_spec,
            target_subprocess_specs,
        )
        if not cls.can_migrate(top_level_bpmn_process_diff, subprocesses_diffs):
            raise ProcessInstanceMigrationNotSafeError(
                f"It is not safe to migrate process instance {process_instance.id} to this version of "
                f"'{process_instance.process_model_identifier}'. This version of the process model may have changed tasks that "
                "have been completed in this process instance or the changes to be made may be too dangerous "
                "to ensure a safe migration."
            )
        return (
            processor,
            target_bpmn_process_spec,
            target_subprocess_specs,
            top_level_bpmn_process_diff,
            subprocesses_diffs,
        )

    @classmethod
    def migrate_process_instance(
        cls,
        process_instance: ProcessInstanceModel,
        user: UserModel,
        preserve_old_process_instance: bool = False,
        target_bpmn_process_hash: str | None = None,
    ) -> None:
        initial_git_revision = process_instance.bpmn_version_control_identifier
        initial_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        (
            processor,
            target_bpmn_process_spec,
            target_subprocess_specs,
            top_level_bpmn_process_diff,
            subprocesses_diffs,
        ) = cls.check_process_instance_can_be_migrated(process_instance, target_bpmn_process_hash=target_bpmn_process_hash)

        migration_task_mask = TaskState.READY | TaskState.WAITING | TaskState.STARTED

        deleted_tasks = migrate_workflow(
            top_level_bpmn_process_diff,
            processor.bpmn_process_instance,
            target_bpmn_process_spec,
            reset_mask=migration_task_mask,
        )
        for sp_id, sp in processor.bpmn_process_instance.subprocesses.items():
            deleted_tasks += migrate_workflow(
                subprocesses_diffs[sp_id],
                sp,
                target_subprocess_specs.get(sp.spec.name),
                reset_mask=migration_task_mask,
            )
            # make sure we change the subprocess_spiff_task state back to STARTED after the migration
            if not sp.is_completed():
                subprocess_spiff_task = processor.bpmn_process_instance.get_task_from_id(sp_id)
                subprocess_spiff_task._set_state(TaskState.STARTED)
        processor.bpmn_process_instance.subprocess_specs = target_subprocess_specs

        if preserve_old_process_instance:
            # TODO: write tests for this code path - no one has a requirement for it yet
            bpmn_process_dict = processor.serialize()
            ProcessInstanceProcessor.update_guids_on_tasks(bpmn_process_dict)
            new_process_instance, _ = cls.create_process_instance_from_process_model_identifier(
                process_instance.process_model_identifier, user
            )
            ProcessInstanceProcessor.persist_bpmn_process_dict(
                bpmn_process_dict, bpmn_definition_to_task_definitions_mappings={}, process_instance_model=new_process_instance
            )
        else:
            future_tasks = TaskModel.query.filter(
                TaskModel.process_instance_id == process_instance.id,
                TaskModel.state.in_(["FUTURE", "MAYBE", "LIKELY"]),  # type: ignore
            ).all()
            for ft in future_tasks:
                db.session.delete(ft)

            bpmn_process_dict = processor.serialize()
            ProcessInstanceProcessor.persist_bpmn_process_dict(
                bpmn_process_dict,
                bpmn_definition_to_task_definitions_mappings={},
                process_instance_model=process_instance,
                bpmn_process_instance=processor.bpmn_process_instance,
                store_process_instance_events=False,
            )
            git_revision_to_use = cls.get_appropriate_git_revision(process_instance, target_bpmn_process_hash)
            process_instance.bpmn_version_control_identifier = git_revision_to_use
            db.session.add(process_instance)

        target_git_revision = process_instance.bpmn_version_control_identifier
        if target_bpmn_process_hash is None:
            target_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        ProcessInstanceTmpService.add_event_to_process_instance(
            process_instance,
            ProcessInstanceEventType.process_instance_migrated.value,
            migration_details={
                "initial_git_revision": initial_git_revision,
                "initial_bpmn_process_hash": initial_bpmn_process_hash or "",
                "target_git_revision": target_git_revision,
                "target_bpmn_process_hash": target_bpmn_process_hash or "",
            },
        )
        deleted_task_guids = [str(dt.id) for dt in deleted_tasks]
        tasks_to_delete = TaskModel.query.filter(TaskModel.guid.in_(deleted_task_guids)).all()  # type: ignore
        bpmn_processes_to_delete = BpmnProcessModel.query.filter(BpmnProcessModel.guid.in_(deleted_task_guids)).all()  # type: ignore
        for td in tasks_to_delete:
            db.session.delete(td)
        for bpd in bpmn_processes_to_delete:
            db.session.delete(bpd)

        user_spiff_tasks = processor.get_ready_user_tasks()
        user_task_guids = [str(t.id) for t in user_spiff_tasks]
        user_spiff_task_map = {str(t.id): t for t in user_spiff_tasks}
        ready_human_tasks = HumanTaskModel.query.filter(HumanTaskModel.task_guid.in_(user_task_guids)).all()  # type: ignore
        for human_task in ready_human_tasks:
            spiff_task = processor.get_task_by_guid(human_task.task_guid)
            potential_owner_hash = processor.get_potential_owners_from_task(spiff_task)
            human_task.update_attributes_from_spiff_task(user_spiff_task_map[human_task.task_guid], potential_owner_hash)
            db.session.add(human_task)
            human_task_user_records = HumanTaskUserModel.query.filter_by(human_task=human_task).all()
            currently_assigned_user_ids = {ht.user_id for ht in human_task_user_records}
            desired_user_ids = {p["user_id"] for p in potential_owner_hash["potential_owners"]}
            user_ids_to_remove = currently_assigned_user_ids - desired_user_ids
            for potential_owner in potential_owner_hash["potential_owners"]:
                if potential_owner["user_id"] not in currently_assigned_user_ids:
                    human_task_user = HumanTaskUserModel(
                        user_id=potential_owner["user_id"], added_by=potential_owner["added_by"], human_task=human_task
                    )
                    db.session.add(human_task_user)
            for htur in human_task_user_records:
                if htur.id in user_ids_to_remove:
                    db.session.delete(htur)

        db.session.commit()

    @classmethod
    def get_appropriate_git_revision(
        cls,
        process_instance: ProcessInstanceModel,
        target_bpmn_process_hash: str | None,
    ) -> str | None:
        # if target_bpmn_process_hash is set and there's an old migration event, then assume this is a revert
        # and that we should ensure that items like git revision remain consistent
        git_revision_to_use = None
        if target_bpmn_process_hash is not None:
            # NOTE: there is a potential bug where there could be many git revisions for a bpmn process hash
            # so this could pick up a different git revision than the revert event passed in.
            # This is an edge case though and the git revision is close enough and more informational
            old_migration_event = (
                ProcessInstanceMigrationDetailModel.query.filter(
                    or_(
                        ProcessInstanceMigrationDetailModel.initial_bpmn_process_hash == target_bpmn_process_hash,
                        ProcessInstanceMigrationDetailModel.target_bpmn_process_hash == target_bpmn_process_hash,
                    )
                )
                .join(ProcessInstanceEventModel)
                .filter(ProcessInstanceEventModel.process_instance_id == process_instance.id)
                .order_by(ProcessInstanceMigrationDetailModel.id.desc())  # type: ignore
                .first()
            )
            if old_migration_event is not None:
                if old_migration_event.initial_bpmn_process_hash == target_bpmn_process_hash:
                    git_revision_to_use = old_migration_event.initial_git_revision
                elif old_migration_event.target_bpmn_process_hash == target_bpmn_process_hash:
                    git_revision_to_use = old_migration_event.target_bpmn_process_hash
        if git_revision_to_use is None:
            try:
                git_revision_to_use = GitService.get_current_revision()
            except GitCommandError:
                pass
        return git_revision_to_use

    @classmethod
    def create_process_instance_from_process_model_identifier(
        cls,
        process_model_identifier: str,
        user: UserModel,
        commit_db: bool = True,
        load_bpmn_process_model: bool = True,
    ) -> ProcessInstanceModel:
        process_model = ProcessModelService.get_process_model(process_model_identifier)
        process_instance_model, (cycle_count, _, duration_in_seconds) = cls.create_process_instance(
            process_model, user, load_bpmn_process_model=load_bpmn_process_model
        )
        cls.register_process_model_cycles(process_model_identifier, cycle_count, duration_in_seconds)
        if commit_db:
            db.session.commit()

        log_extras = {
            "milestone": "Started",
            "process_model_identifier": process_model_identifier,
            "process_instance_id": process_instance_model.id,
        }
        LoggingService.log_event(ProcessInstanceEventType.process_instance_created.value, log_extras)

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
            cls.create_process_instance(
                process_model, process_instance_model.process_initiator, start_configuration, load_bpmn_process_model=False
            )
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
        for ready_user_task in processor.get_ready_user_tasks():
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
                if not queue_process_instance_if_appropriate(process_instance):
                    cls.run_process_instance_with_processor(
                        process_instance, status_value=status_value, execution_strategy_name=execution_strategy_name
                    )
            except ProcessInstanceIsAlreadyLockedError:
                # we will try again later
                continue
            except Exception as exception:
                db.session.rollback()  # in case the above left the database with a bad transaction
                new_exception = Exception(
                    f"Error running {status_value} task for process_instance {process_instance.id}"
                    + f"({process_instance.process_model_identifier}). {exception.__class__.__name__}: {str(exception)}"
                )
                current_app.logger.exception(new_exception, stack_info=True)

    @classmethod
    def run_process_instance_with_processor(
        cls,
        process_instance: ProcessInstanceModel,
        status_value: str | None = None,
        execution_strategy_name: str | None = None,
        should_schedule_waiting_timer_events: bool = True,
    ) -> tuple[ProcessInstanceProcessor | None, TaskRunnability]:
        processor = None
        task_runnability = TaskRunnability.unknown_if_ready_tasks
        with ProcessInstanceQueueService.dequeued(process_instance):
            ProcessInstanceMigrator.run(process_instance)
            processor = ProcessInstanceProcessor(
                process_instance,
                workflow_completed_handler=cls.schedule_next_process_model_cycle,
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
                should_schedule_waiting_timer_events=should_schedule_waiting_timer_events,
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
                            message=f"Spiff Task {spiff_task.task_spec.name} lane user "
                            "dict must have a key called 'value' with the user's uid in it.",
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
                    contents=contents,
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
                    for k, v in collection.items():
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
            if current_app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"] is not None:
                model.store_file_on_file_system()
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
        AuthorizationService.assert_user_can_complete_human_task(process_instance.id, str(spiff_task.id), user)

        # Validate user task data against JSON schema if enabled and it's a User Task (not Manual Task)
        if (
            current_app.config.get("SPIFFWORKFLOW_BACKEND_VALIDATE_USER_TASK_DATA_AGAINST_SCHEMA", False)
            and spiff_task.task_spec.__class__.__name__ == "UserTask"
            and hasattr(spiff_task.task_spec, "extensions")
            and "properties" in spiff_task.task_spec.extensions
            and "formJsonSchemaFilename" in spiff_task.task_spec.extensions["properties"]
        ):
            # The form_schema should already be associated with the task through the task_show endpoint
            # and passed as part of the task model's form_schema property
            task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()
            if task_model is not None:
                form_schema_file_name = spiff_task.task_spec.extensions["properties"]["formJsonSchemaFilename"]

                # Try to get the task's form schema
                from spiffworkflow_backend.routes.process_api_blueprint import _prepare_form_data

                process_model = ProcessModelService.get_process_model(process_instance.process_model_identifier)
                form_schema = _prepare_form_data(
                    form_file=form_schema_file_name,
                    process_model=process_model,
                    task_model=task_model,
                    revision=process_instance.bpmn_version_control_identifier,
                )

                # Validate data against the JSON schema
                try:
                    jsonschema.validate(
                        instance=data,
                        schema=form_schema,
                        format_checker=jsonschema.FormatChecker(),
                    )
                except jsonschema.exceptions.ValidationError as validation_error:
                    # Provide a detailed error message
                    error_message = f"Task data validation failed: {validation_error.message}"
                    if validation_error.path:
                        error_message += f" at path: {'.'.join(str(p) for p in validation_error.path)}"

                    # Raise API error with validation details
                    raise ApiError(
                        error_code="task_data_validation_error", message=error_message, status_code=400
                    ) from validation_error
                except (jsonschema.exceptions.SchemaError, TypeError) as error:
                    # Handle other errors without trying to access .message or .path
                    error_message = f"Task data validation failed: {str(error)}"

                    # Raise API error with validation details
                    raise ApiError(error_code="task_data_validation_error", message=error_message, status_code=400) from error

        # Process file data and merge form data
        cls.save_file_data_and_replace_with_digest_references(
            data,
            process_instance.id,
        )

        if spiff_task.task_spec.__class__.__name__ == "UserTask":
            spiff_task.task_spec.add_data_from_form(spiff_task, data)
        else:
            # this would only affect manual tasks and at some point, we may want to fail instead of updating it
            DeepMerge.merge(spiff_task.data, data)

    @classmethod
    def complete_form_task(
        cls,
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
        data: dict[str, Any],
        user: UserModel,
        human_task: HumanTaskModel,
        execution_mode: str | None = None,
    ) -> None:
        """All the things that need to happen when we complete a form.

        Abstracted here because we need to do it multiple times when completing all tasks in
        a multi-instance task.
        """
        ProcessInstanceService.update_form_task_data(processor.process_instance_model, spiff_task, data, user)
        processor.complete_task(spiff_task, user=user, human_task=human_task)

        # the caller needs to handle the actual queueing of the process instance for better dequeueing ability
        if should_queue_process_instance(execution_mode):
            processor.bpmn_process_instance.refresh_waiting_tasks()
            tasks = processor.bpmn_process_instance.get_tasks(state=TaskState.WAITING | TaskState.READY)
            JinjaService.add_instruction_for_end_user_if_appropriate(tasks, processor.process_instance_model.id, set())
        elif not ProcessInstanceTmpService.is_enqueued_to_run_in_the_future(processor.process_instance_model):
            with sentry_sdk.start_span(op="task", name="backend_do_engine_steps"):
                execution_strategy_name = None
                if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
                    execution_strategy_name = "greedy"

                # maybe move this out once we have the interstitial page since this is
                # here just so we can get the next human task
                processor.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name)

    @staticmethod
    def spiff_task_to_api_task(
        processor: ProcessInstanceProcessor,
        spiff_task: SpiffTask,
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
            AuthorizationService.assert_user_can_complete_human_task(processor.process_instance_model.id, task_guid, g.user)
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

    @classmethod
    def create_and_run_process_instance(
        cls,
        process_model: ProcessModelInfo,
        persistence_level: str,
        data_to_inject: dict | None = None,
        process_id_to_run: str | None = None,
        user: UserModel | None = None,
    ) -> ProcessInstanceProcessor:
        process_instance = None
        if persistence_level == "none":
            BpmnProcessService.persist_bpmn_process_definition(process_model.id)
            user_id = user.id if user is not None else None
            process_instance = ProcessInstanceModel(
                status=ProcessInstanceStatus.not_started.value,
                process_initiator_id=user_id,
                process_model_identifier=process_model.id,
                process_model_display_name=process_model.display_name,
                persistence_level=persistence_level,
            )
        else:
            if user is None:
                raise Exception("User must be provided to create a persistent process instance")
            process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
                process_model.id, user
            )

        processor = None
        try:
            # this is only creates new process instances so no need to worry about process instance migrations
            processor = ProcessInstanceProcessor(
                process_instance,
                script_engine=CustomBpmnScriptEngine(use_restricted_script_engine=False),
                process_id_to_run=process_id_to_run,
            )
            save_to_db = process_instance.persistence_level != "none"
            if data_to_inject is not None:
                processor.do_engine_steps(save=save_to_db, execution_strategy_name="run_current_ready_tasks")
                next_task = processor.next_task()
                DeepMerge.merge(next_task.data, data_to_inject)
            processor.do_engine_steps(save=save_to_db, execution_strategy_name="greedy")
        except (
            ApiError,
            ProcessInstanceIsNotEnqueuedError,
            ProcessInstanceIsAlreadyLockedError,
            WorkflowExecutionServiceError,
        ) as e:
            ErrorHandlingService.handle_error(process_instance, e)
            raise e
        except Exception as e:
            ErrorHandlingService.handle_error(process_instance, e)
            # FIXME: this is going to point someone to the wrong task - it's misinformation for errors in sub-processes.
            # we need to recurse through all last tasks if the last task is a call activity or subprocess.
            if processor is not None:
                task = processor.bpmn_process_instance.last_task
                if task is not None:
                    raise ApiError.from_task(
                        error_code="unknown_exception",
                        message=f"An unknown error occurred. Original error: {e}",
                        status_code=400,
                        task=task,
                    ) from e
            raise e
        return processor

    @classmethod
    def can_migrate(cls, top_level_bpmn_process_diff: WorkflowDiff, subprocesses_diffs: dict[UUID, WorkflowDiff]) -> bool:
        def safe(result: WorkflowDiff) -> bool:
            mask = TaskState.COMPLETED | TaskState.STARTED
            tasks = result.changed + result.removed
            return len(filter_tasks(tasks, state=mask)) == 0

        for diff in subprocesses_diffs.values():
            if diff is None or not safe(diff):
                return False
        return safe(top_level_bpmn_process_diff)

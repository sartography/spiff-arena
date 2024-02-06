from __future__ import annotations

import concurrent.futures
import time
from abc import abstractmethod
from collections.abc import Callable
from datetime import datetime
from typing import Any
from uuid import UUID

import flask.app
from flask import current_app
from flask import g
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.message import MessageEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins.events.event_types import CatchingEvent  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_future_task_if_appropriate,
)
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance_correlation import MessageInstanceCorrelationRuleModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task_instructions_for_end_user import TaskInstructionsForEndUserModel
from spiffworkflow_backend.services.assertion_service import safe_assertion
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.task_service import StartAndEndTimes
from spiffworkflow_backend.services.task_service import TaskService


class WorkflowExecutionServiceError(WorkflowTaskException):  # type: ignore
    @classmethod
    def from_workflow_task_exception(
        cls,
        workflow_task_exception: WorkflowTaskException,
    ) -> WorkflowExecutionServiceError:
        return cls(
            error_msg=str(workflow_task_exception),
            task=workflow_task_exception.task,
            exception=workflow_task_exception,
            line_number=workflow_task_exception.line_number,
            offset=workflow_task_exception.offset,
            error_line=workflow_task_exception.error_line,
        )


class ExecutionStrategyNotConfiguredError(Exception):
    pass


class TaskRunnability(SpiffEnum):
    has_ready_tasks = "has_ready_tasks"
    no_ready_tasks = "no_ready_tasks"
    unknown_if_ready_tasks = "unknown_if_ready_tasks"


class EngineStepDelegate:
    """Interface of sorts for a concrete engine step delegate."""

    @abstractmethod
    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    @abstractmethod
    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    @abstractmethod
    def add_object_to_db_session(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    @abstractmethod
    def after_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    @abstractmethod
    def on_exception(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass


SubprocessSpecLoader = Callable[[], dict[str, Any] | None]


class ExecutionStrategy:
    """Interface of sorts for a concrete execution strategy."""

    def __init__(self, delegate: EngineStepDelegate, subprocess_spec_loader: SubprocessSpecLoader, options: dict | None = None):
        self.delegate = delegate
        self.subprocess_spec_loader = subprocess_spec_loader
        self.options = options

    def should_break_before(self, tasks: list[SpiffTask], process_instance_model: ProcessInstanceModel) -> bool:
        return False

    def should_break_after(self, tasks: list[SpiffTask]) -> bool:
        return False

    def should_do_before(self, bpmn_process_instance: BpmnWorkflow, process_instance_model: ProcessInstanceModel) -> None:
        pass

    def _run(
        self,
        spiff_task: SpiffTask,
        app: flask.app.Flask,
        user: Any | None,
    ) -> SpiffTask:
        with app.app_context():
            g.user = user
            spiff_task.run()
            return spiff_task

    def spiff_run(
        self, bpmn_process_instance: BpmnWorkflow, process_instance_model: ProcessInstanceModel, exit_at: None = None
    ) -> TaskRunnability:
        while True:
            bpmn_process_instance.refresh_waiting_tasks()
            self.should_do_before(bpmn_process_instance, process_instance_model)
            engine_steps = self.get_ready_engine_steps(bpmn_process_instance)
            num_steps = len(engine_steps)
            if self.should_break_before(engine_steps, process_instance_model=process_instance_model):
                task_runnability = TaskRunnability.has_ready_tasks if num_steps > 0 else TaskRunnability.no_ready_tasks
                break
            if num_steps == 0:
                task_runnability = TaskRunnability.no_ready_tasks
                break
            elif num_steps == 1:
                spiff_task = engine_steps[0]
                self.delegate.will_complete_task(spiff_task)
                spiff_task.run()
                self.delegate.did_complete_task(spiff_task)
            elif num_steps > 1:
                # This only works because of the GIL, and the fact that we are not actually executing
                # code in parallel, we are just waiting for I/O in parallel.  So it can run a ton of
                # service tasks at once - many api calls, and then get those responses back without
                # waiting for each individual task to complete.
                futures = []
                user = None
                if hasattr(g, "user"):
                    user = g.user

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    for spiff_task in engine_steps:
                        self.delegate.will_complete_task(spiff_task)
                        futures.append(
                            executor.submit(
                                self._run,
                                spiff_task,
                                current_app._get_current_object(),
                                user,
                            )
                        )
                    for future in concurrent.futures.as_completed(futures):
                        spiff_task = future.result()
                        self.delegate.did_complete_task(spiff_task)
            if self.should_break_after(engine_steps):
                # we could call the stuff at the top of the loop again and find out, but let's not do that unless we need to
                task_runnability = TaskRunnability.unknown_if_ready_tasks
                break

        self.delegate.after_engine_steps(bpmn_process_instance)
        return task_runnability

    def on_exception(self, bpmn_process_instance: BpmnWorkflow) -> None:
        self.delegate.on_exception(bpmn_process_instance)

    def add_object_to_db_session(self, bpmn_process_instance: BpmnWorkflow) -> None:
        self.delegate.add_object_to_db_session(bpmn_process_instance)

    def get_ready_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> list[SpiffTask]:
        tasks = [t for t in bpmn_process_instance.get_tasks(state=TaskState.READY) if not t.task_spec.manual]

        if len(tasks) > 0:
            self.subprocess_spec_loader()

            # TODO: verify the other execution strategies work still and delete to make this work like the name
            # tasks = [tasks[0]]

        return tasks


class TaskModelSavingDelegate(EngineStepDelegate):
    """Engine step delegate that takes care of saving a task model to the database.

    It can also be given another EngineStepDelegate.
    """

    def __init__(
        self,
        serializer: BpmnWorkflowSerializer,
        process_instance: ProcessInstanceModel,
        bpmn_definition_to_task_definitions_mappings: dict,
        secondary_engine_step_delegate: EngineStepDelegate | None = None,
    ) -> None:
        self.secondary_engine_step_delegate = secondary_engine_step_delegate
        self.process_instance = process_instance
        self.bpmn_definition_to_task_definitions_mappings = bpmn_definition_to_task_definitions_mappings
        self.serializer = serializer

        self.current_task_start_in_seconds: float | None = None

        self.last_completed_spiff_task: SpiffTask | None = None
        self.spiff_tasks_to_process: set[UUID] = set()
        self.spiff_task_timestamps: dict[UUID, StartAndEndTimes] = {}

        self.task_service = TaskService(
            process_instance=self.process_instance,
            serializer=self.serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            run_started_at=time.time(),
        )

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        if self._should_update_task_model():
            self.spiff_task_timestamps[spiff_task.id] = {"start_in_seconds": time.time(), "end_in_seconds": None}
            self.current_task_start_in_seconds = time.time()

        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.will_complete_task(spiff_task)

    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        if self._should_update_task_model():
            # NOTE: used with process-all-tasks and process-children-of-last-task
            task_model = self.task_service.update_task_model_with_spiff_task(spiff_task)
            if self.current_task_start_in_seconds is None:
                raise Exception("Could not find cached current_task_start_in_seconds. This should never have happend")
            task_model.start_in_seconds = self.current_task_start_in_seconds
            task_model.end_in_seconds = time.time()

            self.last_completed_spiff_task = spiff_task
        if (
            spiff_task.task_spec.__class__.__name__ in ["StartEvent", "EndEvent", "IntermediateThrowEvent"]
            and spiff_task.task_spec.bpmn_name is not None
        ):
            self.process_instance.last_milestone_bpmn_name = spiff_task.task_spec.bpmn_name
        elif spiff_task.workflow.parent_task_id is None:
            # if parent_task_id is None then this should be the top level process
            if spiff_task.task_spec.__class__.__name__ == "EndEvent":
                self.process_instance.last_milestone_bpmn_name = "Completed"
            elif spiff_task.task_spec.__class__.__name__ == "StartEvent":
                self.process_instance.last_milestone_bpmn_name = "Started"
        self.process_instance.task_updated_at_in_seconds = round(time.time())
        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.did_complete_task(spiff_task)

    def add_object_to_db_session(self, bpmn_process_instance: BpmnWorkflow) -> None:
        # NOTE: process-all-tasks: All tests pass with this but it's less efficient and would be nice to replace
        # excludes COMPLETED. the others were required to get PP1 to go to completion.
        # process FUTURE tasks because Boundary events are not processed otherwise.
        #
        # ANOTHER NOTE: at one point we attempted to be smarter about what tasks we considered for persistence,
        # but it didn't quite work in all cases, so we deleted it. you can find it in commit
        # 1ead87b4b496525df8cc0e27836c3e987d593dc0 if you are curious.
        for waiting_spiff_task in bpmn_process_instance.get_tasks(
            state=TaskState.WAITING
            | TaskState.CANCELLED
            | TaskState.READY
            | TaskState.MAYBE
            | TaskState.LIKELY
            | TaskState.FUTURE
            | TaskState.STARTED
            | TaskState.ERROR,
        ):
            self.task_service.update_task_model_with_spiff_task(waiting_spiff_task)

        self.task_service.save_objects_to_database()

        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.add_object_to_db_session(bpmn_process_instance)

    def after_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass

    def on_exception(self, bpmn_process_instance: BpmnWorkflow) -> None:
        self.after_engine_steps(bpmn_process_instance)

    def _should_update_task_model(self) -> bool:
        """No reason to save task model stuff if the process instance isn't persistent."""
        return self.process_instance.persistence_level != "none"


class GreedyExecutionStrategy(ExecutionStrategy):
    """
    This is what the base class does by default.
    """

    pass


class QueueInstructionsForEndUserExecutionStrategy(ExecutionStrategy):
    """When you want to run tasks with instructionsForEndUser but you want to queue them.

    The queue can be used to display the instructions to user later.
    """

    def __init__(self, delegate: EngineStepDelegate, subprocess_spec_loader: SubprocessSpecLoader, options: dict | None = None):
        super().__init__(delegate, subprocess_spec_loader, options)
        self.tasks_that_have_been_seen: set[str] = set()

    def should_do_before(self, bpmn_process_instance: BpmnWorkflow, process_instance_model: ProcessInstanceModel) -> None:
        tasks = bpmn_process_instance.get_tasks(state=TaskState.WAITING | TaskState.READY)
        for spiff_task in tasks:
            if hasattr(spiff_task.task_spec, "extensions") and spiff_task.task_spec.extensions.get(
                "instructionsForEndUser", None
            ):
                task_guid = str(spiff_task.id)
                if task_guid in self.tasks_that_have_been_seen:
                    continue
                instruction = JinjaService.render_instructions_for_end_user(spiff_task)
                if instruction != "":
                    TaskInstructionsForEndUserModel.insert_or_update_record(
                        task_guid=str(spiff_task.id),
                        process_instance_id=process_instance_model.id,
                        instruction=instruction,
                    )
                    self.tasks_that_have_been_seen.add(str(spiff_task.id))

    def should_break_before(self, tasks: list[SpiffTask], process_instance_model: ProcessInstanceModel) -> bool:
        for spiff_task in tasks:
            if hasattr(spiff_task.task_spec, "extensions") and spiff_task.task_spec.extensions.get(
                "instructionsForEndUser", None
            ):
                return True
        return False


class RunUntilUserTaskOrMessageExecutionStrategy(ExecutionStrategy):
    """When you want to run tasks until you hit something to report to the end user.

    Note that this will run at least one engine step if possible,
    but will stop if it hits instructions after the first task.
    """

    def should_break_before(self, tasks: list[SpiffTask], process_instance_model: ProcessInstanceModel) -> bool:
        for spiff_task in tasks:
            if hasattr(spiff_task.task_spec, "extensions") and spiff_task.task_spec.extensions.get(
                "instructionsForEndUser", None
            ):
                return True
        return False


class RunCurrentReadyTasksExecutionStrategy(ExecutionStrategy):
    """When you want to run only one engine step at a time."""

    def should_break_after(self, tasks: list[SpiffTask]) -> bool:
        return True


class SkipOneExecutionStrategy(ExecutionStrategy):
    """When you want to skip over the next task, rather than execute it."""

    def spiff_run(
        self, bpmn_process_instance: BpmnWorkflow, process_instance_model: ProcessInstanceModel, exit_at: None = None
    ) -> TaskRunnability:
        spiff_task = None
        engine_steps = []
        if self.options and "spiff_task" in self.options.keys():
            spiff_task = self.options["spiff_task"]
        else:
            engine_steps = self.get_ready_engine_steps(bpmn_process_instance)
            if len(engine_steps) > 0:
                spiff_task = engine_steps[0]
        if spiff_task is not None:
            self.delegate.will_complete_task(spiff_task)
            spiff_task.complete()
            self.delegate.did_complete_task(spiff_task)
        self.delegate.after_engine_steps(bpmn_process_instance)
        # even if there was just 1 engine_step, and we ran it, we can't know that there is not another one
        # that resulted from running that one, hence the unknown_if_ready_tasks
        return TaskRunnability.has_ready_tasks if len(engine_steps) > 1 else TaskRunnability.unknown_if_ready_tasks


def execution_strategy_named(name: str, delegate: EngineStepDelegate, spec_loader: SubprocessSpecLoader) -> ExecutionStrategy:
    cls = {
        "greedy": GreedyExecutionStrategy,
        "queue_instructions_for_end_user": QueueInstructionsForEndUserExecutionStrategy,
        "run_until_user_message": RunUntilUserTaskOrMessageExecutionStrategy,
        "run_current_ready_tasks": RunCurrentReadyTasksExecutionStrategy,
        "skip_one": SkipOneExecutionStrategy,
    }[name]

    return cls(delegate, spec_loader)


ProcessInstanceCompleter = Callable[[BpmnWorkflow], None]
ProcessInstanceSaver = Callable[[], None]


class WorkflowExecutionService:
    """Provides the driver code for workflow execution."""

    def __init__(
        self,
        bpmn_process_instance: BpmnWorkflow,
        process_instance_model: ProcessInstanceModel,
        execution_strategy: ExecutionStrategy,
        process_instance_completer: ProcessInstanceCompleter,
        process_instance_saver: ProcessInstanceSaver,
        additional_processing_identifier: str | None = None,
    ):
        self.bpmn_process_instance = bpmn_process_instance
        self.process_instance_model = process_instance_model
        self.execution_strategy = execution_strategy
        self.process_instance_completer = process_instance_completer
        self.process_instance_saver = process_instance_saver
        self.additional_processing_identifier = additional_processing_identifier

    # names of methods that do spiff stuff:
    # processor.do_engine_steps calls:
    #   run
    #     execution_strategy.spiff_run
    #       spiff.[some_run_task_method]
    def run_and_save(self, exit_at: None = None, save: bool = False) -> TaskRunnability:
        if self.process_instance_model.persistence_level != "none":
            with safe_assertion(
                ProcessInstanceLockService.has_lock(
                    self.process_instance_model.id, additional_processing_identifier=self.additional_processing_identifier
                )
            ) as tripped:
                if tripped:
                    raise AssertionError(
                        "The current thread has not obtained a lock for this process"
                        f" instance ({self.process_instance_model.id})."
                    )
        try:
            self.bpmn_process_instance.refresh_waiting_tasks()

            # TODO: implicit re-entrant locks here `with_dequeued`
            task_runnability = self.execution_strategy.spiff_run(
                self.bpmn_process_instance, exit_at=exit_at, process_instance_model=self.process_instance_model
            )

            if self.bpmn_process_instance.is_completed():
                self.process_instance_completer(self.bpmn_process_instance)

            self.process_bpmn_messages()
            self.queue_waiting_receive_messages()
            self.schedule_waiting_timer_events()
            return task_runnability
        except WorkflowTaskException as wte:
            ProcessInstanceTmpService.add_event_to_process_instance(
                self.process_instance_model,
                ProcessInstanceEventType.task_failed.value,
                exception=wte,
                task_guid=str(wte.task.id),
            )
            self.execution_strategy.on_exception(self.bpmn_process_instance)
            raise WorkflowExecutionServiceError.from_workflow_task_exception(wte) from wte
        except SpiffWorkflowException as swe:
            self.execution_strategy.on_exception(self.bpmn_process_instance)
            raise ApiError.from_workflow_exception("task_error", str(swe), swe) from swe

        finally:
            if self.process_instance_model.persistence_level != "none":
                # even if a task fails, try to persist all tasks, which will include the error state.
                self.execution_strategy.add_object_to_db_session(self.bpmn_process_instance)
                if save:
                    self.process_instance_saver()

    def is_happening_soon(self, time_in_seconds: int) -> bool:
        # if it is supposed to happen in less than the amount of time we take between polling runs
        return time_in_seconds - time.time() < int(
            current_app.config["SPIFFWORKFLOW_BACKEND_BACKGROUND_SCHEDULER_FUTURE_TASK_EXECUTION_INTERVAL_IN_SECONDS"]
        )

    def schedule_waiting_timer_events(self) -> None:
        # TODO: update to always insert records so we can remove user_input_required and possibly waiting apscheduler jobs
        if current_app.config["SPIFFWORKFLOW_BACKEND_CELERY_ENABLED"]:
            waiting_tasks = self.bpmn_process_instance.get_tasks(state=TaskState.WAITING, spec_class=CatchingEvent)
            for spiff_task in waiting_tasks:
                event = spiff_task.task_spec.event_definition.details(spiff_task)
                if "Time" in event.event_type:
                    time_string = event.value
                    run_at_in_seconds = round(datetime.fromisoformat(time_string).timestamp())
                    FutureTaskModel.insert_or_update(guid=str(spiff_task.id), run_at_in_seconds=run_at_in_seconds)
                    if self.is_happening_soon(run_at_in_seconds):
                        queue_future_task_if_appropriate(
                            self.process_instance_model, eta_in_seconds=run_at_in_seconds, task_guid=str(spiff_task.id)
                        )

    def process_bpmn_messages(self) -> None:
        # FIXE: get_events clears out the events so if we have other events we care about
        #   this will clear them out as well.
        # Right now we only care about messages though.
        bpmn_events = self.bpmn_process_instance.get_events()
        for bpmn_event in bpmn_events:
            if not isinstance(bpmn_event.event_definition, MessageEventDefinition):
                continue
            bpmn_message = bpmn_event.event_definition
            message_instance = MessageInstanceModel(
                process_instance_id=self.process_instance_model.id,
                user_id=self.process_instance_model.process_initiator_id,
                # TODO: use the correct swimlane user when that is set up
                message_type="send",
                name=bpmn_message.name,
                payload=bpmn_event.payload,
                correlation_keys=self.bpmn_process_instance.correlations,
            )
            db.session.add(message_instance)

            bpmn_process = self.process_instance_model.bpmn_process
            if bpmn_process is not None:
                bpmn_process_correlations = self.bpmn_process_instance.correlations
                bpmn_process.properties_json["correlations"] = bpmn_process_correlations
                # update correlations correctly but always null out bpmn_messages since they get cleared out later
                bpmn_process.properties_json["bpmn_events"] = []
                db.session.add(bpmn_process)

    def queue_waiting_receive_messages(self) -> None:
        waiting_events = self.bpmn_process_instance.waiting_events()
        waiting_message_events = filter(lambda e: e.event_type == "MessageEventDefinition", waiting_events)
        for event in waiting_message_events:
            # Ensure we are only creating one active message instance for each waiting message
            if (
                MessageInstanceModel.query.filter_by(
                    process_instance_id=self.process_instance_model.id,
                    message_type="receive",
                    name=event.name,
                    status="ready",
                ).count()
                > 0
            ):
                continue

            # Create a new Message Instance
            message_instance = MessageInstanceModel(
                process_instance_id=self.process_instance_model.id,
                user_id=self.process_instance_model.process_initiator_id,
                message_type="receive",
                name=event.name,
                correlation_keys=self.bpmn_process_instance.correlations,
            )
            for correlation_property in event.value:
                message_correlation = MessageInstanceCorrelationRuleModel(
                    message_instance=message_instance,
                    name=correlation_property.name,
                    retrieval_expression=correlation_property.retrieval_expression,
                    correlation_key_names=correlation_property.correlation_keys,
                )
                db.session.add(message_correlation)
            db.session.add(message_instance)

            bpmn_process = self.process_instance_model.bpmn_process

            if bpmn_process is not None:
                bpmn_process_correlations = self.bpmn_process_instance.correlations
                bpmn_process.properties_json["correlations"] = bpmn_process_correlations
                db.session.add(bpmn_process)


class ProfiledWorkflowExecutionService(WorkflowExecutionService):
    """A profiled version of the workflow execution service."""

    def run_and_save(self, exit_at: None = None, save: bool = False) -> TaskRunnability:
        import cProfile
        from pstats import SortKey

        task_runnability = TaskRunnability.unknown_if_ready_tasks
        with cProfile.Profile() as pr:
            task_runnability = super().run_and_save(exit_at=exit_at, save=save)
        pr.print_stats(sort=SortKey.CUMULATIVE)
        return task_runnability

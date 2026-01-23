from __future__ import annotations

import concurrent.futures
import sys
import time
from abc import abstractmethod
from collections.abc import Callable
from datetime import datetime
from threading import Lock
from typing import Any
from uuid import UUID

# ExceptionGroup is built-in in Python 3.11+, but needs backport for 3.10
if sys.version_info < (3, 11):
    try:
        from exceptiongroup import ExceptionGroup
    except ImportError:
        pass  # Runtime will catch NameError if not available

import flask.app
from flask import current_app
from flask import g
from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.control import BoundaryEventJoin  # type: ignore
from SpiffWorkflow.bpmn.specs.control import BoundaryEventSplit
from SpiffWorkflow.bpmn.specs.control import UnstructuredJoin
from SpiffWorkflow.bpmn.specs.event_definitions.item_aware_event import CodeEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.message import MessageEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins import SubWorkflowTaskMixin  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins.events.event_types import CatchingEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins.events.intermediate_event import BoundaryEvent  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskFilter  # type: ignore
from SpiffWorkflow.util.task import TaskState

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_future_task_if_appropriate,
)
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance import MessageStatuses
from spiffworkflow_backend.models.message_instance_correlation import MessageInstanceCorrelationRuleModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.assertion_service import safe_assertion
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.logging_service import LoggingService
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
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

    @classmethod
    def from_completion_with_unhandled_events(
        cls,
        task: SpiffTask,
        unhandled_events: dict[str, list[Any]],
    ) -> WorkflowExecutionServiceError:
        events = {k: [e.event_definition.code for e in v] for k, v in unhandled_events.items()}

        return cls(
            error_msg=f"The process completed with unhandled events: {events}",
            task=task,
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

    @abstractmethod
    def last_completed_spiff_task(self) -> SpiffTask | None:
        pass


class ExecutionStrategy:
    """Interface of sorts for a concrete execution strategy."""

    _mutex = Lock()

    def __init__(self, delegate: EngineStepDelegate, options: dict | None = None):
        self.delegate = delegate
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
        process_model_identifier: str,
        process_instance_id: int,
    ) -> SpiffTask:
        with app.app_context():
            tld = current_app.config.get("THREAD_LOCAL_DATA")
            if tld:
                tld.process_model_identifier = process_model_identifier
                tld.process_instance_id = process_instance_id

            g.user = user

            should_lock = any(isinstance(child.task_spec, SubWorkflowTaskMixin) for child in spiff_task.children)

            if should_lock:
                with self._mutex:
                    spiff_task.run()
            else:
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
                user = None
                if hasattr(g, "user"):
                    user = g.user

                # When a task with a gateway is completed it marks the gateway as either WAITING or READY.
                # The problem is if two of these parent tasks mark their gateways as READY then both are processed
                # and end up being marked completed, when in fact only one gateway attached to the same bpmn bpmn_id
                # is allowed to be READY/COMPLETED. If two are READY and execute, then the tasks after the gateway will
                # be unintentially duplicated.
                has_gateway_children = False
                for spiff_task in engine_steps:
                    for child_task in spiff_task.children:
                        if isinstance(child_task.task_spec, UnstructuredJoin):
                            has_gateway_children = True

                if current_app.config["SPIFFWORKFLOW_BACKEND_USE_THREADS_FOR_TASK_EXECUTION"] and not has_gateway_children:
                    self._run_engine_steps_with_threads(engine_steps, process_instance_model, user)
                else:
                    self._run_engine_steps_without_threads(engine_steps, process_instance_model, user)

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
        task_filter = TaskFilter(state=TaskState.READY, manual=False)
        steps = list(
            bpmn_process_instance.get_tasks(
                first_task=self.delegate.last_completed_spiff_task(),
                task_filter=task_filter,
            )
        )

        # This ensures that escalations and errors that have code specified take precedence over those that do not
        code, no_code = [], []
        for task in steps:
            spec = task.task_spec
            if not isinstance(spec, BoundaryEvent) or not isinstance(spec.event_definition, CodeEventDefinition):
                continue
            if spec.event_definition.code is None:
                no_code.append(task)
            else:
                code.append(task)

        if len(code) > 0 and len(no_code) > 0:
            for task in no_code:
                steps.remove(task)
                task.cancel()

        if not steps:
            steps = list(
                bpmn_process_instance.get_tasks(
                    task_filter=task_filter,
                )
            )

        return steps

    def _run_engine_steps_with_threads(
        self, engine_steps: list[SpiffTask], process_instance: ProcessInstanceModel, user: UserModel | None
    ) -> None:
        # This only works because of the GIL, and the fact that we are not actually executing
        # code in parallel, we are just waiting for I/O in parallel.  So it can run a ton of
        # service tasks at once - many api calls, and then get those responses back without
        # waiting for each individual task to complete.
        futures = []
        future_to_task = {}
        with concurrent.futures.ThreadPoolExecutor() as executor:
            for spiff_task in engine_steps:
                self.delegate.will_complete_task(spiff_task)
                future = executor.submit(
                    self._run,
                    spiff_task,
                    current_app._get_current_object(),
                    user,
                    process_instance.process_model_identifier,
                    process_instance.id,
                )
                futures.append(future)
                future_to_task[id(future)] = spiff_task

            exceptions = []
            completed_tasks = []
            for future in concurrent.futures.as_completed(futures):
                try:
                    spiff_task = future.result()
                    completed_tasks.append(spiff_task)
                except Exception as exception:
                    failed_task = future_to_task[id(future)]
                    task_info = (
                        f"Task: {failed_task.task_spec.name} (bpmn_name: {failed_task.task_spec.bpmn_name}, id: {failed_task.id})"
                    )
                    exception.args = (f"{task_info} - {str(exception)}",)
                    exceptions.append(exception)

            for spiff_task in completed_tasks:
                self.delegate.did_complete_task(spiff_task)

            if exceptions:
                # Try to use ExceptionGroup (Python 3.11+), fall back to raising first exception
                try:
                    exception_strings = [str(exception) for exception in exceptions]
                    msg = f"{len(exceptions)} task(s) failed during parallel {exception_strings}"

                    raise ExceptionGroup(msg, exceptions)
                except NameError:
                    if len(exceptions) > 1:
                        for exc in exceptions[1:]:
                            current_app.logger.error(f"Additional task failure during parallel execution: {exc}", exc_info=exc)
                    raise exceptions[0] from None

    def _run_engine_steps_without_threads(
        self, engine_steps: list[SpiffTask], process_instance: ProcessInstanceModel, user: UserModel | None
    ) -> None:
        for spiff_task in engine_steps:
            self.delegate.will_complete_task(spiff_task)
            self._run(
                spiff_task,
                current_app._get_current_object(),
                user,
                process_instance.process_model_identifier,
                process_instance.id,
            )
            self.delegate.did_complete_task(spiff_task)


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
        task_model_mapping: dict[str, TaskModel] | None = None,
        bpmn_subprocess_mapping: dict[str, BpmnProcessModel] | None = None,
    ) -> None:
        self.secondary_engine_step_delegate = secondary_engine_step_delegate
        self.process_instance = process_instance
        self.bpmn_definition_to_task_definitions_mappings = bpmn_definition_to_task_definitions_mappings
        self.serializer = serializer

        self.current_task_start_in_seconds: float | None = None

        self._last_completed_spiff_task: SpiffTask | None = None
        self.spiff_tasks_to_process: set[UUID] = set()
        self.spiff_task_timestamps: dict[UUID, StartAndEndTimes] = {}

        self.task_service = TaskService(
            process_instance=self.process_instance,
            serializer=self.serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
            run_started_at=time.time(),
            task_model_mapping=task_model_mapping,
            bpmn_subprocess_mapping=bpmn_subprocess_mapping,
        )

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        if self._should_update_task_model():
            self.spiff_task_timestamps[spiff_task.id] = {"start_in_seconds": time.time(), "end_in_seconds": None}
            self.current_task_start_in_seconds = time.time()

        KKVDataStore.add_data_store_getters_to_spiff_task(spiff_task)

        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.will_complete_task(spiff_task)

    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        if self._should_update_task_model():
            # NOTE: used with process-all-tasks and process-children-of-last-task
            task_model = self.task_service.update_task_model_with_spiff_task(spiff_task)
            if self.current_task_start_in_seconds is None:
                raise Exception("Could not find cached current_task_start_in_seconds. This should never have happened")
            task_model.start_in_seconds = self.current_task_start_in_seconds
            task_model.end_in_seconds = time.time()

        metadata = ProcessModelService.extract_metadata(
            self.process_instance.process_model_identifier,
            spiff_task.data,
        )
        log_extras = {
            "task_id": str(spiff_task.id),
            "task_spec": spiff_task.task_spec.name,
            "bpmn_name": spiff_task.task_spec.bpmn_name,
            "process_model_identifier": self.process_instance.process_model_identifier,
            "process_instance_id": self.process_instance.id,
            "metadata": metadata,
        }
        if (
            spiff_task.task_spec.__class__.__name__ in ["StartEvent", "EndEvent", "IntermediateThrowEvent"]
            and spiff_task.task_spec.bpmn_name is not None
        ):
            self.process_instance.last_milestone_bpmn_name = spiff_task.task_spec.bpmn_name
            log_extras["milestone"] = spiff_task.task_spec.bpmn_name
            if current_app.config.get("SPIFFWORKFLOW_BACKEND_LOG_MILESTONES"):
                current_app.logger.info(f"Milestone completed: {spiff_task.task_spec.bpmn_name}", extra={"extras": log_extras})
        elif spiff_task.workflow.parent_task_id is None:
            # if parent_task_id is None then this should be the top level process
            if spiff_task.task_spec.__class__.__name__ == "EndEvent":
                self.process_instance.last_milestone_bpmn_name = "Completed"
            elif spiff_task.task_spec.__class__.__name__ == "StartEvent":
                self.process_instance.last_milestone_bpmn_name = "Started"

        LoggingService.log_event(ProcessInstanceEventType.task_completed.value, log_extras)
        self.process_instance.task_updated_at_in_seconds = round(time.time())
        # This ensures boundary events attached to a task are prioritized
        # The default is to continue along a branch as long as possible, but this can allow subprocesses to
        # complete before any boundary events can cancel it.
        # Once a boundary event split is reached, don't update the search start until the corresponding join is reached.
        if self._last_completed_spiff_task is None or not isinstance(
            self._last_completed_spiff_task.task_spec, BoundaryEventSplit
        ):
            self._last_completed_spiff_task = spiff_task
        elif (
            isinstance(spiff_task.task_spec, BoundaryEventJoin)
            and spiff_task.task_spec.split_task == self._last_completed_spiff_task.task_spec.name
        ):
            self._last_completed_spiff_task = spiff_task

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

    def get_guid_to_db_object_mappings(self) -> tuple[dict[str, TaskModel], dict[str, BpmnProcessModel]]:
        return self.task_service.get_guid_to_db_object_mappings()

    def _should_update_task_model(self) -> bool:
        """No reason to save task model stuff if the process instance isn't persistent."""
        return self.process_instance.persistence_level != "none"

    def last_completed_spiff_task(self) -> SpiffTask | None:
        return self._last_completed_spiff_task


class GreedyExecutionStrategy(ExecutionStrategy):
    """
    This is what the base class does by default.
    """

    pass


class QueueInstructionsForEndUserExecutionStrategy(ExecutionStrategy):
    """When you want to run tasks with instructionsForEndUser but you want to queue them.

    The queue can be used to display the instructions to user later.
    """

    def __init__(self, delegate: EngineStepDelegate, options: dict | None = None):
        super().__init__(delegate, options)
        self.tasks_that_have_been_seen: set[str] = set()

    def should_do_before(self, bpmn_process_instance: BpmnWorkflow, process_instance_model: ProcessInstanceModel) -> None:
        tasks = bpmn_process_instance.get_tasks(state=TaskState.WAITING | TaskState.READY)
        JinjaService.add_instruction_for_end_user_if_appropriate(tasks, process_instance_model.id, self.tasks_that_have_been_seen)

    def should_break_before(self, tasks: list[SpiffTask], process_instance_model: ProcessInstanceModel) -> bool:
        # exit if there are instructionsForEndUser so the instructions can be comitted to the db using the normal save method
        # for the process instance.
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


def execution_strategy_named(name: str, delegate: EngineStepDelegate) -> ExecutionStrategy:
    cls = {
        "greedy": GreedyExecutionStrategy,
        "queue_instructions_for_end_user": QueueInstructionsForEndUserExecutionStrategy,
        "run_until_user_message": RunUntilUserTaskOrMessageExecutionStrategy,
        "run_current_ready_tasks": RunCurrentReadyTasksExecutionStrategy,
        "skip_one": SkipOneExecutionStrategy,
    }[name]

    return cls(delegate)


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
    ):
        self.bpmn_process_instance = bpmn_process_instance
        self.process_instance_model = process_instance_model
        self.execution_strategy = execution_strategy
        self.process_instance_completer = process_instance_completer
        self.process_instance_saver = process_instance_saver

    # names of methods that do spiff stuff:
    # processor.do_engine_steps calls:
    #   run
    #     execution_strategy.spiff_run
    #       spiff.[some_run_task_method]
    def run_and_save(
        self,
        exit_at: None = None,
        save: bool = False,
        should_schedule_waiting_timer_events: bool = True,
        profile: bool = False,
        needs_dequeue: bool = True,
    ) -> TaskRunnability:
        if profile:
            import cProfile
            from pstats import SortKey

            task_runnability = TaskRunnability.unknown_if_ready_tasks
            with cProfile.Profile() as pr:
                task_runnability = self._run_and_save(
                    exit_at, save, should_schedule_waiting_timer_events, needs_dequeue=needs_dequeue
                )
            pr.print_stats(sort=SortKey.CUMULATIVE)
            return task_runnability

        return self._run_and_save(exit_at, save, should_schedule_waiting_timer_events, needs_dequeue=needs_dequeue)

    def _run_and_save(
        self,
        exit_at: None = None,
        save: bool = False,
        should_schedule_waiting_timer_events: bool = True,
        needs_dequeue: bool = True,
    ) -> TaskRunnability:
        if needs_dequeue and self.process_instance_model.persistence_level != "none":
            with safe_assertion(ProcessInstanceLockService.has_lock(self.process_instance_model.id)) as tripped:
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

            self.process_bpmn_events()
            self.queue_waiting_receive_messages()
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
                    if should_schedule_waiting_timer_events:
                        self.schedule_waiting_timer_events()

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
                    queued_to_run_at_in_seconds = None
                    if self.is_happening_soon(run_at_in_seconds):
                        if queue_future_task_if_appropriate(
                            self.process_instance_model, eta_in_seconds=run_at_in_seconds, task_guid=str(spiff_task.id)
                        ):
                            queued_to_run_at_in_seconds = run_at_in_seconds
                    FutureTaskModel.insert_or_update(
                        guid=str(spiff_task.id),
                        run_at_in_seconds=run_at_in_seconds,
                        queued_to_run_at_in_seconds=queued_to_run_at_in_seconds,
                    )

    def group_bpmn_events(self) -> dict[str, Any]:
        event_groups: dict[str, Any] = {}
        for bpmn_event in self.bpmn_process_instance.get_events():
            key = type(bpmn_event.event_definition).__name__
            if key not in event_groups:
                event_groups[key] = []
            event_groups[key].append(bpmn_event)
        return event_groups

    def process_bpmn_events(self) -> None:
        bpmn_event_groups = self.group_bpmn_events()
        message_events = bpmn_event_groups.pop(MessageEventDefinition.__name__, [])

        if bpmn_event_groups:
            raise WorkflowExecutionServiceError.from_completion_with_unhandled_events(
                self.bpmn_process_instance.last_task, bpmn_event_groups
            )

        self.process_bpmn_messages(message_events)

    def process_bpmn_messages(self, bpmn_events: list[MessageEventDefinition]) -> None:
        for bpmn_event in bpmn_events:
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
        waiting_message_events = list(filter(lambda e: e.event_type == "MessageEventDefinition", waiting_events))

        waiting_message_names = {event.name for event in waiting_message_events}

        # Cancel any ready message instances that no longer have corresponding waiting events
        existing_ready_messages = MessageInstanceModel.query.filter_by(
            process_instance_id=self.process_instance_model.id,
            message_type="receive",
            status="ready",
        ).all()
        existing_ready_message_names = set()
        for message_instance in existing_ready_messages:
            if message_instance.name not in waiting_message_names:
                message_instance.status = MessageStatuses.cancelled.value
                db.session.add(message_instance)
            else:
                existing_ready_message_names.add(message_instance.name)

        for event in waiting_message_events:
            # Ensure we are only creating one active message instance for each waiting message
            if event.name in existing_ready_message_names:
                continue

            # Create a new Message Instance
            message_instance = MessageInstanceModel(
                process_instance_id=self.process_instance_model.id,
                user_id=self.process_instance_model.process_initiator_id,
                message_type="receive",
                name=event.name,
                correlation_keys=event.correlations,
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

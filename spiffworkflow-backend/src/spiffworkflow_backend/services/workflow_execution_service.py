from __future__ import annotations

import copy
import time
from abc import abstractmethod
from collections.abc import Callable
from typing import Any
from uuid import UUID

from SpiffWorkflow.bpmn.exceptions import WorkflowTaskException  # type: ignore
from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.message import MessageEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance_correlation import MessageInstanceCorrelationRuleModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.services.assertion_service import safe_assertion
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


class EngineStepDelegate:
    """Interface of sorts for a concrete engine step delegate."""

    @abstractmethod
    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    @abstractmethod
    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    @abstractmethod
    def save(self, bpmn_process_instance: BpmnWorkflow, commit: bool = False) -> None:
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

    def __init__(
        self, delegate: EngineStepDelegate, subprocess_spec_loader: SubprocessSpecLoader, options: dict | None = None
    ):
        self.delegate = delegate
        self.subprocess_spec_loader = subprocess_spec_loader
        self.options = options

    @abstractmethod
    def spiff_run(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        pass

    def on_exception(self, bpmn_process_instance: BpmnWorkflow) -> None:
        self.delegate.on_exception(bpmn_process_instance)

    def save(self, bpmn_process_instance: BpmnWorkflow) -> None:
        self.delegate.save(bpmn_process_instance)

    def get_ready_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> list[SpiffTask]:
        tasks = [t for t in bpmn_process_instance.get_tasks(TaskState.READY) if not t.task_spec.manual]

        if len(tasks) > 0:
            self.subprocess_spec_loader()
            tasks = [tasks[0]]

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
        )

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        if self._should_update_task_model():
            self.spiff_task_timestamps[spiff_task.id] = {"start_in_seconds": time.time(), "end_in_seconds": None}
            spiff_task.task_spec._predict(spiff_task, mask=TaskState.NOT_FINISHED_MASK)

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

            # # NOTE: used with process-spiff-tasks-list
            # self.spiff_task_timestamps[spiff_task.id]['end_in_seconds'] = time.time()
            # self.spiff_tasks_to_process.add(spiff_task.id)
            # self._add_children(spiff_task)
            # # self._add_parents(spiff_task)

            self.last_completed_spiff_task = spiff_task
        self.process_instance.task_updated_at_in_seconds = round(time.time())
        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.did_complete_task(spiff_task)

    def save(self, bpmn_process_instance: BpmnWorkflow, _commit: bool = True) -> None:
        self.task_service.save_objects_to_database()

        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.save(bpmn_process_instance, commit=False)
        db.session.commit()

    def after_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> None:
        if self._should_update_task_model():
            # NOTE: process-all-tasks: All tests pass with this but it's less efficient and would be nice to replace
            # excludes COMPLETED. the others were required to get PP1 to go to completion.
            # process FUTURE tasks because Boundary events are not processed otherwise.
            for waiting_spiff_task in bpmn_process_instance.get_tasks(
                TaskState.WAITING
                | TaskState.CANCELLED
                | TaskState.READY
                | TaskState.MAYBE
                | TaskState.LIKELY
                | TaskState.FUTURE
                | TaskState.STARTED
                | TaskState.ERROR
            ):
                # these will be removed from the parent and then ignored
                if waiting_spiff_task._has_state(TaskState.PREDICTED_MASK):
                    continue

                # removing elements from an array causes the loop to exit so deep copy the array first
                waiting_children = copy.copy(waiting_spiff_task.children)
                for waiting_child in waiting_children:
                    if waiting_child._has_state(TaskState.PREDICTED_MASK):
                        waiting_spiff_task.children.remove(waiting_child)

                self.task_service.update_task_model_with_spiff_task(waiting_spiff_task)

            # # NOTE: process-spiff-tasks-list: this would be the ideal way to handle all tasks
            # # but we're missing something with it yet
            # #
            # # adding from line here until we are ready to go with this
            # from SpiffWorkflow.exceptions import TaskNotFoundException
            # for spiff_task_uuid in self.spiff_tasks_to_process:
            #     try:
            #         waiting_spiff_task = bpmn_process_instance.get_task_from_id(spiff_task_uuid)
            #     except TaskNotFoundException:
            #         continue
            #
            #     # include PREDICTED_MASK tasks in list so we can remove them from the parent
            #     if waiting_spiff_task._has_state(TaskState.PREDICTED_MASK):
            #         TaskService.remove_spiff_task_from_parent(waiting_spiff_task, self.task_service.task_models)
            #         for cpt in waiting_spiff_task.parent.children:
            #             if cpt.id == waiting_spiff_task.id:
            #                 waiting_spiff_task.parent.children.remove(cpt)
            #         continue
            #     # if waiting_spiff_task.state == TaskState.FUTURE:
            #     #     continue
            #     start_and_end_times = None
            #     if waiting_spiff_task.id in self.spiff_task_timestamps:
            #         start_and_end_times = self.spiff_task_timestamps[waiting_spiff_task.id]
            #     self.task_service.update_task_model_with_spiff_task(waiting_spiff_task, start_and_end_times=start_and_end_times)
            #
            # if self.last_completed_spiff_task is not None:
            #     self.task_service.process_spiff_task_parent_subprocess_tasks(self.last_completed_spiff_task)

            # # NOTE: process-children-of-last-task: this does not work with escalation boundary events
            # if self.last_completed_spiff_task is not None:
            #     self.task_service.process_spiff_task_children(self.last_completed_spiff_task)
            #     self.task_service.process_spiff_task_parent_subprocess_tasks(self.last_completed_spiff_task)

    def on_exception(self, bpmn_process_instance: BpmnWorkflow) -> None:
        self.after_engine_steps(bpmn_process_instance)

    def _add_children(self, spiff_task: SpiffTask) -> None:
        for child_spiff_task in spiff_task.children:
            self.spiff_tasks_to_process.add(child_spiff_task.id)
            self._add_children(child_spiff_task)

    def _add_parents(self, spiff_task: SpiffTask) -> None:
        if spiff_task.parent and spiff_task.parent.task_spec.name != "Root":
            self.spiff_tasks_to_process.add(spiff_task.parent.id)
            self._add_parents(spiff_task.parent)

    def _should_update_task_model(self) -> bool:
        """No reason to save task model stuff if the process instance isn't persistent."""
        return self.process_instance.persistence_level != "none"


class GreedyExecutionStrategy(ExecutionStrategy):
    """The common execution strategy. This will greedily run all engine steps without stopping."""

    def spiff_run(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        self.bpmn_process_instance = bpmn_process_instance
        self.run_until_user_input_required(exit_at)
        self.delegate.after_engine_steps(bpmn_process_instance)

    def run_until_user_input_required(self, exit_at: None = None) -> None:
        """Keeps running tasks until there are no non-human READY tasks.

        spiff.refresh_waiting_tasks is the thing that pushes some waiting tasks to READY.
        """
        engine_steps = self.get_ready_engine_steps(self.bpmn_process_instance)
        while engine_steps:
            for spiff_task in engine_steps:
                self.delegate.will_complete_task(spiff_task)
                spiff_task.run()
                self.delegate.did_complete_task(spiff_task)
                self.bpmn_process_instance.refresh_waiting_tasks()
            engine_steps = self.get_ready_engine_steps(self.bpmn_process_instance)


class RunUntilServiceTaskExecutionStrategy(ExecutionStrategy):
    """For illustration purposes, not currently integrated.

    Would allow the `run` from the UI to execute until a service task then
    return (to an interstitial page). The background processor would then take over.
    """

    def spiff_run(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        engine_steps = self.get_ready_engine_steps(bpmn_process_instance)
        while engine_steps:
            for spiff_task in engine_steps:
                if spiff_task.task_spec.description == "Service Task":
                    return
                self.delegate.will_complete_task(spiff_task)
                spiff_task.run()
                self.delegate.did_complete_task(spiff_task)
                bpmn_process_instance.refresh_waiting_tasks()
            engine_steps = self.get_ready_engine_steps(bpmn_process_instance)
        self.delegate.after_engine_steps(bpmn_process_instance)


class RunUntilUserTaskOrMessageExecutionStrategy(ExecutionStrategy):
    """When you want to run tasks until you hit something to report to the end user.

    Note that this will run at least one engine step if possible,
    but will stop if it hits instructions after the first task.
    """

    def spiff_run(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        should_continue = True
        bpmn_process_instance.refresh_waiting_tasks()
        engine_steps = self.get_ready_engine_steps(bpmn_process_instance)
        while engine_steps and should_continue:
            for task in engine_steps:
                if hasattr(task.task_spec, "extensions") and task.task_spec.extensions.get(
                    "instructionsForEndUser", None
                ):
                    should_continue = False
                    break
                self.delegate.will_complete_task(task)
                task.run()
                self.delegate.did_complete_task(task)
            bpmn_process_instance.refresh_waiting_tasks()
            engine_steps = self.get_ready_engine_steps(bpmn_process_instance)
        self.delegate.after_engine_steps(bpmn_process_instance)


class OneAtATimeExecutionStrategy(ExecutionStrategy):
    """When you want to run only one engine step at a time."""

    def spiff_run(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        engine_steps = self.get_ready_engine_steps(bpmn_process_instance)
        if len(engine_steps) > 0:
            spiff_task = engine_steps[0]
            self.delegate.will_complete_task(spiff_task)
            spiff_task.run()
            self.delegate.did_complete_task(spiff_task)
        self.delegate.after_engine_steps(bpmn_process_instance)


class SkipOneExecutionStrategy(ExecutionStrategy):
    """When you want to to skip over the next task, rather than execute it."""

    def spiff_run(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        spiff_task = None
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


def execution_strategy_named(
    name: str, delegate: EngineStepDelegate, spec_loader: SubprocessSpecLoader
) -> ExecutionStrategy:
    cls = {
        "greedy": GreedyExecutionStrategy,
        "run_until_service_task": RunUntilServiceTaskExecutionStrategy,
        "run_until_user_message": RunUntilUserTaskOrMessageExecutionStrategy,
        "one_at_a_time": OneAtATimeExecutionStrategy,
        "skip_one": SkipOneExecutionStrategy,
    }[name]

    return cls(delegate, spec_loader)  # type: ignore


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
    def run_and_save(self, exit_at: None = None, save: bool = False) -> None:
        if self.process_instance_model.persistence_level != "none":
            with safe_assertion(ProcessInstanceLockService.has_lock(self.process_instance_model.id)) as tripped:
                if tripped:
                    raise AssertionError(
                        "The current thread has not obtained a lock for this process"
                        f" instance ({self.process_instance_model.id})."
                    )

        try:
            self.bpmn_process_instance.refresh_waiting_tasks()

            # TODO: implicit re-entrant locks here `with_dequeued`
            self.execution_strategy.spiff_run(self.bpmn_process_instance, exit_at)

            if self.bpmn_process_instance.is_completed():
                self.process_instance_completer(self.bpmn_process_instance)

            if self.process_instance_model.persistence_level != "none":
                self.process_bpmn_messages()
                self.queue_waiting_receive_messages()
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
                self.execution_strategy.save(self.bpmn_process_instance)
                db.session.commit()

                if save:
                    self.process_instance_saver()

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

            db.session.commit()

    def queue_waiting_receive_messages(self) -> None:
        waiting_events = self.bpmn_process_instance.waiting_events()
        waiting_message_events = filter(lambda e: e.event_type == "MessageEventDefinition", waiting_events)
        for event in waiting_message_events:
            # Ensure we are only creating one message instance for each waiting message
            if (
                MessageInstanceModel.query.filter_by(
                    process_instance_id=self.process_instance_model.id,
                    message_type="receive",
                    name=event.name,
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

            db.session.commit()


class ProfiledWorkflowExecutionService(WorkflowExecutionService):
    """A profiled version of the workflow execution service."""

    def run_and_save(self, exit_at: None = None, save: bool = False) -> None:
        import cProfile
        from pstats import SortKey

        with cProfile.Profile() as pr:
            super().run_and_save(exit_at=exit_at, save=save)
        pr.print_stats(sort=SortKey.CUMULATIVE)

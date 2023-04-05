import time
from typing import Callable
from typing import Set
import json
from typing import Optional
from uuid import UUID

from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException, TaskNotFoundException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance_correlation import (
    MessageInstanceCorrelationRuleModel,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel  # noqa: F401
from spiffworkflow_backend.services.assertion_service import safe_assertion
from spiffworkflow_backend.services.process_instance_lock_service import (
    ProcessInstanceLockService,
)
from spiffworkflow_backend.services.task_service import TaskService


class EngineStepDelegate:
    """Interface of sorts for a concrete engine step delegate."""

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    def save(self, bpmn_process_instance: BpmnWorkflow, commit: bool = False) -> None:
        pass

    def after_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass


class TaskModelSavingDelegate(EngineStepDelegate):
    """Engine step delegate that takes care of saving a task model to the database.

    It can also be given another EngineStepDelegate.
    """

    def __init__(
        self,
        serializer: BpmnWorkflowSerializer,
        process_instance: ProcessInstanceModel,
        bpmn_definition_to_task_definitions_mappings: dict,
        secondary_engine_step_delegate: Optional[EngineStepDelegate] = None,
    ) -> None:
        self.secondary_engine_step_delegate = secondary_engine_step_delegate
        self.process_instance = process_instance
        self.bpmn_definition_to_task_definitions_mappings = bpmn_definition_to_task_definitions_mappings
        self.serializer = serializer

        self.current_task_model: Optional[TaskModel] = None
        self.current_task_start_in_seconds: Optional[float] = None

        self.last_completed_spiff_task: Optional[SpiffTask] = None
        self.spiff_tasks_to_process: Set[UUID] = set()

        self.task_service = TaskService(
            process_instance=self.process_instance,
            serializer=self.serializer,
            bpmn_definition_to_task_definitions_mappings=self.bpmn_definition_to_task_definitions_mappings,
        )

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        if self._should_update_task_model():
            # if spiff_task.task_spec.name == 'passing_script_task':
            #     import pdb; pdb.set_trace()
            #     print("HEY1")
            self.current_task_start_in_seconds = time.time()
            spiff_task.task_spec._predict(spiff_task, mask=TaskState.NOT_FINISHED_MASK)
        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.will_complete_task(spiff_task)

    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        if self._should_update_task_model():
            # if spiff_task.task_spec.name == 'test_process_to_call_script.BoundaryEventParent':
            #     import pdb; pdb.set_trace()
            #     print("HEY")
            task_model = self.task_service.update_task_model_with_spiff_task(spiff_task)
            if self.current_task_start_in_seconds is None:
                raise Exception("Could not find cached current_task_start_in_seconds. This should never have happend")
            task_model.start_in_seconds = self.current_task_start_in_seconds
            task_model.end_in_seconds = time.time()
            self.last_completed_spiff_task = spiff_task
            self.spiff_tasks_to_process.add(spiff_task.id)
            self._add_children(spiff_task)
            self._add_parents(spiff_task)

            # self.task_service.process_spiff_task_parent_subprocess_tasks(spiff_task)
            # self.task_service.process_spiff_task_children(spiff_task)
        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.did_complete_task(spiff_task)

    def save(self, bpmn_process_instance: BpmnWorkflow, _commit: bool = True) -> None:
        script_engine = bpmn_process_instance.script_engine
        if hasattr(script_engine, "failing_spiff_task") and script_engine.failing_spiff_task is not None:
            failing_spiff_task = script_engine.failing_spiff_task
            self.task_service.update_task_model_with_spiff_task(failing_spiff_task, task_failed=True)
            self.task_service.process_spiff_task_parent_subprocess_tasks(failing_spiff_task)
            self.task_service.process_spiff_task_children(failing_spiff_task)

        self.task_service.save_objects_to_database()

        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.save(bpmn_process_instance, commit=False)
        db.session.commit()

    def _add_children(self, spiff_task: SpiffTask) -> None:
        for child_spiff_task in spiff_task.children:
            self.spiff_tasks_to_process.add(child_spiff_task.id)
            self._add_children(child_spiff_task)

    def _add_parents(self, spiff_task: SpiffTask) -> None:
        if spiff_task.parent and spiff_task.parent.task_spec.name != "Root":
            self.spiff_tasks_to_process.add(spiff_task.parent.id)
            self._add_parents(spiff_task.parent)

    def after_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> None:
        if self._should_update_task_model():
            # excludes COMPLETED. the others were required to get PP1 to go to completion.
            # process FUTURE tasks because Boundary events are not processed otherwise.
            # for waiting_spiff_task in bpmn_process_instance.get_tasks(
            #     TaskState.WAITING | TaskState.CANCELLED | TaskState.READY | TaskState.MAYBE | TaskState.LIKELY | TaskState.FUTURE
            # ):
            for spiff_task_guid in self.spiff_tasks_to_process:
                if spiff_task_guid is None:
                    continue
                try:
                    print(f"spiff_task_guid: {spiff_task_guid}")
                    waiting_spiff_task = bpmn_process_instance.get_task_from_id(spiff_task_guid)
                except TaskNotFoundException:
                    continue
                # if waiting_spiff_task.task_spec.name == 'top_level_manual_task_two':
                #     import pdb; pdb.set_trace()
                #     print("HEY42")
                # include PREDICTED_MASK tasks in list so we can remove them from the parent
                if waiting_spiff_task._has_state(TaskState.PREDICTED_MASK):
                    TaskService.remove_spiff_task_from_parent(waiting_spiff_task, self.task_service.task_models)
                    for cpt in waiting_spiff_task.parent.children:
                        if cpt.id == waiting_spiff_task.id:
                           waiting_spiff_task.parent.children.remove(cpt)
                    continue
                try:
                    self.task_service.update_task_model_with_spiff_task(waiting_spiff_task)
                except Exception as ex:
                    import pdb; pdb.set_trace()
                    print("HEY16")
                # self.task_service.process_spiff_task_parent_subprocess_tasks(waiting_spiff_task)

            # if self.last_completed_spiff_task is not None:
            #     self.task_service.process_spiff_task_parent_subprocess_tasks(self.last_completed_spiff_task)
            #     self.task_service.process_spiff_task_children(self.last_completed_spiff_task)

    def _should_update_task_model(self) -> bool:
        """We need to figure out if we have previously save task info on this process intance.

        Use the bpmn_process_id to do this.
        """
        # return self.process_instance.bpmn_process_id is not None
        return True


class ExecutionStrategy:
    """Interface of sorts for a concrete execution strategy."""

    def __init__(self, delegate: EngineStepDelegate):
        """__init__."""
        self.delegate = delegate

    def do_engine_steps(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        pass

    def save(self, bpmn_process_instance: BpmnWorkflow) -> None:
        self.delegate.save(bpmn_process_instance)


class GreedyExecutionStrategy(ExecutionStrategy):
    """The common execution strategy. This will greedily run all engine steps without stopping."""

    def do_engine_steps(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        self.bpmn_process_instance = bpmn_process_instance
        bpmn_process_instance.do_engine_steps(
            exit_at=exit_at,
            will_complete_task=self.delegate.will_complete_task,
            did_complete_task=self.delegate.did_complete_task,
        )
        self.delegate.after_engine_steps(bpmn_process_instance)


class RunUntilServiceTaskExecutionStrategy(ExecutionStrategy):
    """For illustration purposes, not currently integrated.

    Would allow the `run` from the UI to execute until a service task then
    return (to an interstitial page). The background processor would then take over.
    """

    def do_engine_steps(self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None) -> None:
        self.bpmn_process_instance = bpmn_process_instance
        engine_steps = list(
            [
                t
                for t in bpmn_process_instance.get_tasks(TaskState.READY)
                if bpmn_process_instance._is_engine_task(t.task_spec)
            ]
        )
        while engine_steps:
            for spiff_task in engine_steps:
                if spiff_task.task_spec.spec_type == "Service Task":
                    return
                self.delegate.will_complete_task(spiff_task)
                spiff_task.complete()
                self.delegate.did_complete_task(spiff_task)

            engine_steps = list(
                [
                    t
                    for t in bpmn_process_instance.get_tasks(TaskState.READY)
                    if bpmn_process_instance._is_engine_task(t.task_spec)
                ]
            )

        self.delegate.after_engine_steps(bpmn_process_instance)


def execution_strategy_named(name: str, delegate: EngineStepDelegate) -> ExecutionStrategy:
    cls = {
        "greedy": GreedyExecutionStrategy,
        "run_until_service_task": RunUntilServiceTaskExecutionStrategy,
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
        """__init__."""
        self.bpmn_process_instance = bpmn_process_instance
        self.process_instance_model = process_instance_model
        self.execution_strategy = execution_strategy
        self.process_instance_completer = process_instance_completer
        self.process_instance_saver = process_instance_saver

    def do_engine_steps(self, exit_at: None = None, save: bool = False) -> None:
        """Do_engine_steps."""
        with safe_assertion(ProcessInstanceLockService.has_lock(self.process_instance_model.id)) as tripped:
            if tripped:
                raise AssertionError(
                    "The current thread has not obtained a lock for this process"
                    f" instance ({self.process_instance_model.id})."
                )

        try:
            self.bpmn_process_instance.refresh_waiting_tasks()

            # TODO: implicit re-entrant locks here `with_dequeued`
            self.execution_strategy.do_engine_steps(self.bpmn_process_instance, exit_at)

            if self.bpmn_process_instance.is_completed():
                self.process_instance_completer(self.bpmn_process_instance)

            self.process_bpmn_messages()
            self.queue_waiting_receive_messages()
        except SpiffWorkflowException as swe:
            raise swe
            raise ApiError.from_workflow_exception("task_error", str(swe), swe) from swe

        finally:
            self.execution_strategy.save(self.bpmn_process_instance)
            db.session.commit()

            if save:
                self.process_instance_saver()

    def process_bpmn_messages(self) -> None:
        """Process_bpmn_messages."""
        bpmn_messages = self.bpmn_process_instance.get_bpmn_messages()
        for bpmn_message in bpmn_messages:
            message_instance = MessageInstanceModel(
                process_instance_id=self.process_instance_model.id,
                user_id=self.process_instance_model.process_initiator_id,  # TODO: use the correct swimlane user when that is set up
                message_type="send",
                name=bpmn_message.name,
                payload=bpmn_message.payload,
                correlation_keys=self.bpmn_process_instance.correlations,
            )
            db.session.add(message_instance)

            bpmn_process = self.process_instance_model.bpmn_process
            if bpmn_process is not None:
                bpmn_process_correlations = self.bpmn_process_instance.correlations
                bpmn_process.properties_json["correlations"] = bpmn_process_correlations
                db.session.add(bpmn_process)

            db.session.commit()

    def queue_waiting_receive_messages(self) -> None:
        """Queue_waiting_receive_messages."""
        waiting_events = self.bpmn_process_instance.waiting_events()
        waiting_message_events = filter(lambda e: e["event_type"] == "Message", waiting_events)

        for event in waiting_message_events:
            # Ensure we are only creating one message instance for each waiting message
            if (
                MessageInstanceModel.query.filter_by(
                    process_instance_id=self.process_instance_model.id,
                    message_type="receive",
                    name=event["name"],
                ).count()
                > 0
            ):
                continue

            # Create a new Message Instance
            message_instance = MessageInstanceModel(
                process_instance_id=self.process_instance_model.id,
                user_id=self.process_instance_model.process_initiator_id,
                message_type="receive",
                name=event["name"],
                correlation_keys=self.bpmn_process_instance.correlations,
            )
            for correlation_property in event["value"]:
                message_correlation = MessageInstanceCorrelationRuleModel(
                    message_instance_id=message_instance.id,
                    name=correlation_property.name,
                    retrieval_expression=correlation_property.retrieval_expression,
                )
                message_instance.correlation_rules.append(message_correlation)
            db.session.add(message_instance)

            bpmn_process = self.process_instance_model.bpmn_process

            if bpmn_process is not None:
                bpmn_process_correlations = self.bpmn_process_instance.correlations
                bpmn_process.properties_json["correlations"] = bpmn_process_correlations
                db.session.add(bpmn_process)

            db.session.commit()


class ProfiledWorkflowExecutionService(WorkflowExecutionService):
    """A profiled version of the workflow execution service."""

    def do_engine_steps(self, exit_at: None = None, save: bool = False) -> None:
        """__do_engine_steps."""
        import cProfile
        from pstats import SortKey

        with cProfile.Profile() as pr:
            super().do_engine_steps(exit_at=exit_at, save=save)
        pr.print_stats(sort=SortKey.CUMULATIVE)

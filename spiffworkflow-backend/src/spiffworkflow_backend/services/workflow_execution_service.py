import logging
import time
from typing import Callable
from typing import List
from typing import Optional

from SpiffWorkflow.bpmn.serializer.workflow import BpmnWorkflowSerializer  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance_correlation import (
    MessageInstanceCorrelationRuleModel,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.spiff_step_details import SpiffStepDetailsModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.task_service import JsonDataDict
from spiffworkflow_backend.services.task_service import TaskService


class EngineStepDelegate:
    """Interface of sorts for a concrete engine step delegate."""

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        pass

    def save(self, commit: bool = False) -> None:
        pass

    def after_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> None:
        pass


SpiffStepIncrementer = Callable[[], None]
SpiffStepDetailsMappingBuilder = Callable[[SpiffTask, float, float], dict]


class TaskModelSavingDelegate(EngineStepDelegate):
    """Engine step delegate that takes care of saving a task model to the database.

    It can also be given another EngineStepDelegate.
    """

    def __init__(
        self,
        serializer: BpmnWorkflowSerializer,
        process_instance: ProcessInstanceModel,
        secondary_engine_step_delegate: Optional[EngineStepDelegate] = None,
    ) -> None:
        self.secondary_engine_step_delegate = secondary_engine_step_delegate
        self.process_instance = process_instance

        self.current_task_model: Optional[TaskModel] = None
        self.task_models: dict[str, TaskModel] = {}
        self.json_data_dicts: dict[str, JsonDataDict] = {}
        self.serializer = serializer

    def should_update_task_model(self) -> bool:
        """We need to figure out if we have previously save task info on this process intance.

        Use the bpmn_process_id to do this.
        """
        return self.process_instance.bpmn_process_id is not None

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        if self.should_update_task_model():
            _bpmn_process, task_model, new_task_models, new_json_data_dicts = (
                TaskService.find_or_create_task_model_from_spiff_task(
                    spiff_task, self.process_instance, self.serializer
                )
            )
            self.current_task_model = task_model
            self.task_models.update(new_task_models)
            self.json_data_dicts.update(new_json_data_dicts)
            self.current_task_model.start_in_seconds = time.time()
        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.will_complete_task(spiff_task)

    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        if self.current_task_model and self.should_update_task_model():
            self.current_task_model.end_in_seconds = time.time()
            json_data_dict = TaskService.update_task_model(
                self.current_task_model, spiff_task, self.serializer
            )
            if json_data_dict is not None:
                self.json_data_dicts[json_data_dict["hash"]] = json_data_dict
            self.task_models[self.current_task_model.guid] = self.current_task_model
        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.did_complete_task(spiff_task)

    def save(self, _commit: bool = True) -> None:
        db.session.bulk_save_objects(self.task_models.values())

        TaskService.insert_or_update_json_data_records(self.json_data_dicts)

        if self.secondary_engine_step_delegate:
            self.secondary_engine_step_delegate.save(commit=False)
        db.session.commit()

    def after_engine_steps(self, bpmn_process_instance: BpmnWorkflow) -> None:
        if self.should_update_task_model():
            # excludes FUTURE and COMPLETED. the others were required to get PP1 to go to completion.
            for waiting_spiff_task in bpmn_process_instance.get_tasks(
                TaskState.WAITING
                | TaskState.CANCELLED
                | TaskState.READY
                | TaskState.MAYBE
                | TaskState.LIKELY
            ):
                _bpmn_process, task_model, new_task_models, new_json_data_dicts = (
                    TaskService.find_or_create_task_model_from_spiff_task(
                        waiting_spiff_task, self.process_instance, self.serializer
                    )
                )
                self.task_models.update(new_task_models)
                self.json_data_dicts.update(new_json_data_dicts)
                json_data_dict = TaskService.update_task_model(
                    task_model, waiting_spiff_task, self.serializer
                )
                self.task_models[task_model.guid] = task_model
                if json_data_dict is not None:
                    self.json_data_dicts[json_data_dict["hash"]] = json_data_dict


class StepDetailLoggingDelegate(EngineStepDelegate):
    """Engine step delegate that takes care of logging spiff step details.

    This separates the concerns of step execution and step logging.
    """

    def __init__(
        self,
        increment_spiff_step: SpiffStepIncrementer,
        spiff_step_details_mapping: SpiffStepDetailsMappingBuilder,
    ):
        """__init__."""
        self.increment_spiff_step = increment_spiff_step
        self.spiff_step_details_mapping = spiff_step_details_mapping
        self.step_details: List[dict] = []
        self.current_task_start_in_seconds = 0.0
        self.tasks_to_log = {
            "BPMN Task",
            "Script Task",
            "Service Task",
            "Default Start Event",
            "Exclusive Gateway",
            "Call Activity",
            # "End Join",
            "End Event",
            "Default Throwing Event",
            "Subprocess",
            "Transactional Subprocess",
        }

    def should_log(self, spiff_task: SpiffTask) -> bool:
        return (
            spiff_task.task_spec.spec_type in self.tasks_to_log
            and not spiff_task.task_spec.name.endswith(".EndJoin")
        )

    def will_complete_task(self, spiff_task: SpiffTask) -> None:
        if self.should_log(spiff_task):
            self.current_task_start_in_seconds = time.time()
            self.increment_spiff_step()

    def did_complete_task(self, spiff_task: SpiffTask) -> None:
        if self.should_log(spiff_task):
            self.step_details.append(
                self.spiff_step_details_mapping(
                    spiff_task, self.current_task_start_in_seconds, time.time()
                )
            )

    def save(self, commit: bool = True) -> None:
        db.session.bulk_insert_mappings(SpiffStepDetailsModel, self.step_details)
        if commit:
            db.session.commit()


class ExecutionStrategy:
    """Interface of sorts for a concrete execution strategy."""

    def __init__(self, delegate: EngineStepDelegate):
        """__init__."""
        self.delegate = delegate

    def do_engine_steps(
        self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None
    ) -> None:
        pass

    def save(self) -> None:
        self.delegate.save()


class GreedyExecutionStrategy(ExecutionStrategy):
    """The common execution strategy. This will greedily run all engine step without stopping."""

    def do_engine_steps(
        self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None
    ) -> None:
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

    def do_engine_steps(
        self, bpmn_process_instance: BpmnWorkflow, exit_at: None = None
    ) -> None:
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


def execution_strategy_named(
    name: str, delegate: EngineStepDelegate
) -> ExecutionStrategy:
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
        try:
            self.bpmn_process_instance.refresh_waiting_tasks()

            self.execution_strategy.do_engine_steps(self.bpmn_process_instance, exit_at)

            if self.bpmn_process_instance.is_completed():
                self.process_instance_completer(self.bpmn_process_instance)

            self.process_bpmn_messages()
            self.queue_waiting_receive_messages()
        except SpiffWorkflowException as swe:
            raise ApiError.from_workflow_exception("task_error", str(swe), swe) from swe

        finally:
            self.execution_strategy.save()
            spiff_logger = logging.getLogger("spiff")
            for handler in spiff_logger.handlers:
                if hasattr(handler, "bulk_insert_logs"):
                    handler.bulk_insert_logs()  # type: ignore
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
        waiting_message_events = filter(
            lambda e: e["event_type"] == "Message", waiting_events
        )

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

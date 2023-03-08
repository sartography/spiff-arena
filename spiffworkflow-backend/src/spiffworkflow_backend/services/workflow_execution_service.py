from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel

from typing import Callable, Optional

class EngineStepDelegate:
    """TODO: comment."""
    def will_complete_task(task: SpiffTask) -> None:
        pass

    def did_complete_task(task: SpiffTask) -> None:
        pass

    def save() -> None:
        pass

SpiffStepIncrementer = Callable[[], None]
SpiffStepDetailsMappingBuilder = Callable[[SpiffTask, float, float], dict]

class StepDetailLoggingEngineStepDelegate(EngineStepDelegate):
    """TODO: comment."""
    def __init__(self,
        increment_spiff_step: SpiffStepIncrementer,
        spiff_step_details_mapping: SpiffStepDetailsMappingBuilder,
    ):
        self.increment_spiff_step = increment_spiff_step
        self.spiff_step_details_mapping = spiff_step_details_mapping
        self.step_details = []
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

        def should_log(task: SpiffTask) -> bool:
            return (
                task.task_spec.spec_type in self.tasks_to_log
                and not task.task_spec.name.endswith(".EndJoin")
            )

        def will_complete_task(task: SpiffTask) -> None:
            if should_log(task):
                self.current_task_start_in_seconds = time.time()
                self.increment_spiff_step()

        def did_complete_task(task: SpiffTask) -> None:
            if should_log(task):
                step_details.append(
                    self.spiff_step_details_mapping(
                        task, self.current_task_start_in_seconds, time.time()
                    )
                )

    def save() -> None:
        db.session.bulk_insert_mappings(SpiffStepDetailsModel, step_details)
        db.session.commit()

class ExecutionStrategy:
    """TODO: comment."""
    def __init__(self, bpmn_process_instance: BpmnWorkflow, delegate: EngineStepDelegate):
        self.bpmn_process_instance = bpmn_process_instance
        self.delegate = delegate

    def do_engine_steps(self, exit_at: None = None) -> None:
        pass
    
    def save() -> None:
        self.delegate.save()

class GreedyExecutionStrategy(ExecutionStrategy):
    """TODO: comment."""
    def do_engine_steps(self, exit_at: None = None) -> None:
        self.bpmn_process_instance.do_engine_steps(
            exit_at=exit_at,
            will_complete_task=will_complete_task,
            did_complete_task=did_complete_task,
        )

ProcessInstanceCompleter = Callable[[BpmnWorkflow], None]
SaveHandler = Callable[[], None]

class WorkflowExecutionService:
    """TODO: comment."""
    def __init__(self,
        bpmn_process_instance: BpmnWorkflow,
        process_instance_model: ProcessInstanceModel,
        execution_strategy: ExecutionStrategy, 
        process_instance_completer: ProcessInstanceCompleter,
        save_handler: SaveHandler,
    ):
        self.bpmn_process_instance = bpmn_process_instance
        self.process_instance_model = process_instance_model
        self.execution_strategy = execution_strategy
        self.process_instance_completer = process_instance_completer
        self.save_handler = save_handler
    
    def do_engine_steps(self, exit_at: None = None, save: bool = False) -> None:
        """Do_engine_steps."""

        try:
            self.bpmn_process_instance.refresh_waiting_tasks()

            self.execution_strategy.do_engine_steps(exit_at)

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
                self.save_handler()

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
            db.session.commit()

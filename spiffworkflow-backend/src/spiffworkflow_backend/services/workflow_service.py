"""workflow_service."""
from datetime import datetime

from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from spiffworkflow_backend.specs.start_event import StartConfiguration
from spiffworkflow_backend.specs.start_event import StartEvent


class WorkflowService:
    """WorkflowService."""

    @classmethod
    def future_start_events(cls, workflow: BpmnWorkflow) -> list[SpiffTask]:
        return [t for t in workflow.get_tasks(TaskState.FUTURE) if isinstance(t.task_spec, StartEvent)]

    @classmethod
    def next_start_event_configuration(cls, workflow: BpmnWorkflow, now_in_utc: datetime) -> StartConfiguration | None:
        start_events = cls.future_start_events(workflow)
        configurations = list(
            map(
                lambda start_event: start_event.task_spec.configuration(start_event, now_in_utc),  # type: ignore
                start_events,
            )
        )
        configurations.sort(key=lambda configuration: configuration[1])  # type: ignore
        return configurations[0] if len(configurations) > 0 else None

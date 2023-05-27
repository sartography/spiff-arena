"""workflow_service."""
from datetime import datetime

from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.task import TaskState
from spiffworkflow_backend.specs.start_event import StartEvent


class WorkflowService:
    """WorkflowService."""

    @classmethod
    def future_start_events(cls, workflow: BpmnWorkflow) -> list[SpiffTask]:
        return [t for t in workflow.get_tasks(TaskState.FUTURE) if isinstance(t.task_spec, StartEvent)]

    @classmethod
    def next_start_event_delay_in_seconds(cls, workflow: BpmnWorkflow, now_in_utc: datetime) -> int:
        start_events = cls.future_start_events(workflow)
        start_delays: list[int] = []
        for start_event in start_events:
            start_delay = start_event.task_spec.start_delay_in_seconds(start_event, now_in_utc)
            start_delays.append(start_delay)
        start_delays.sort()
        return start_delays[0] if len(start_delays) > 0 else 0

    @classmethod
    def calculate_run_at_delay_in_seconds(cls, workflow: BpmnWorkflow, now_in_utc: datetime) -> int:
        # TODO: for now we are using the first start time because I am not sure how multiple
        # start events should work. I think the right answer is to take the earliest start
        # time and have later start events stay FUTURE/WAITING?, then we need to be able
        # to respect the other start events when enqueue'ing.
        #
        # TODO: this method should also expand to include other FUTURE/WAITING timers when
        # enqueue'ing so that we don't have to check timers every 10 or whatever seconds
        # right now we assume that this is being called to create a process

        return cls.next_start_event_delay_in_seconds(workflow, now_in_utc)

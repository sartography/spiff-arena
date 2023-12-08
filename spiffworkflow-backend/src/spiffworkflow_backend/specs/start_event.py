from datetime import datetime
from datetime import timedelta
from typing import Any

from SpiffWorkflow.bpmn.parser.util import full_tag  # type: ignore
from SpiffWorkflow.bpmn.specs.defaults import StartEvent as DefaultStartEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.simple import NoneEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.timer import CycleTimerEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.timer import DurationTimerEventDefinition
from SpiffWorkflow.bpmn.specs.event_definitions.timer import TimeDateEventDefinition
from SpiffWorkflow.bpmn.specs.event_definitions.timer import TimerEventDefinition
from SpiffWorkflow.spiff.parser.event_parsers import SpiffStartEventParser  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

StartConfiguration = tuple[int, int, int]

# TODO: cycle timers and repeat counts?


class StartEvent(DefaultStartEvent):  # type: ignore
    def __init__(self, wf_spec, bpmn_id, event_definition, **kwargs):  # type: ignore
        if isinstance(event_definition, TimerEventDefinition):
            super().__init__(wf_spec, bpmn_id, NoneEventDefinition(), **kwargs)
            self.timer_definition = event_definition
        else:
            super().__init__(wf_spec, bpmn_id, event_definition, **kwargs)
            self.timer_definition = None

    @staticmethod
    def register_parser_class(parser_config: dict[str, Any]) -> None:
        parser_config[full_tag("startEvent")] = (SpiffStartEventParser, StartEvent)

    def configuration(self, my_task: SpiffTask, now_in_utc: datetime) -> StartConfiguration:
        evaluated_expression = self.evaluated_timer_expression(my_task)
        cycles = 0
        duration = 0
        time_delta = timedelta(seconds=0)

        if evaluated_expression is not None:
            if isinstance(self.timer_definition, TimeDateEventDefinition):
                parsed_duration = TimerEventDefinition.parse_time_or_duration(evaluated_expression)
                time_delta = parsed_duration - now_in_utc
            elif isinstance(self.timer_definition, DurationTimerEventDefinition):
                parsed_duration = TimerEventDefinition.parse_iso_duration(evaluated_expression)
                time_delta = TimerEventDefinition.get_timedelta_from_start(parsed_duration, now_in_utc)
            elif isinstance(self.timer_definition, CycleTimerEventDefinition):
                cycles, start, cycle_duration = TimerEventDefinition.parse_iso_recurring_interval(evaluated_expression)
                time_delta = start - now_in_utc
                duration = int(cycle_duration.total_seconds())

        start_delay_in_seconds = int(time_delta.total_seconds())

        return (cycles, start_delay_in_seconds, duration)

    def evaluated_timer_expression(self, my_task: SpiffTask) -> Any:
        script_engine = my_task.workflow.script_engine
        evaluated_expression = None

        if isinstance(self.timer_definition, TimerEventDefinition) and script_engine is not None:
            evaluated_expression = script_engine.evaluate(my_task, self.timer_definition.expression)
        return evaluated_expression

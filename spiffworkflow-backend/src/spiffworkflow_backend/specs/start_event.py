from datetime import datetime
from datetime import timedelta
from typing import Any
from typing import Dict, Optional, Tuple

from SpiffWorkflow.bpmn.parser.util import full_tag  # type: ignore
from SpiffWorkflow.bpmn.serializer.task_spec import EventConverter  # type: ignore
from SpiffWorkflow.bpmn.serializer.task_spec import StartEventConverter as DefaultStartEventConverter
from SpiffWorkflow.bpmn.specs.defaults import StartEvent as DefaultStartEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions import CycleTimerEventDefinition  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions import DurationTimerEventDefinition
from SpiffWorkflow.bpmn.specs.event_definitions import NoneEventDefinition
from SpiffWorkflow.bpmn.specs.event_definitions import TimeDateEventDefinition
from SpiffWorkflow.bpmn.specs.event_definitions import TimerEventDefinition
from SpiffWorkflow.spiff.parser.event_parsers import SpiffStartEventParser  # type: ignore
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from flask import current_app

# TODO: cylce timers and repeat counts?
class StartEvent(DefaultStartEvent):  # type: ignore
    def __init__(self, wf_spec, bpmn_id, event_definition, **kwargs):  # type: ignore
        if isinstance(event_definition, TimerEventDefinition):
            super().__init__(wf_spec, bpmn_id, NoneEventDefinition(), **kwargs)
            self.timer_definition = event_definition
        else:
            super().__init__(wf_spec, bpmn_id, event_definition, **kwargs)
            self.timer_definition = None

    @staticmethod
    def register_converter(spec_config: Dict[str, Any]) -> None:
        spec_config["task_specs"].remove(DefaultStartEventConverter)
        spec_config["task_specs"].append(StartEventConverter)

    @staticmethod
    def register_parser_class(parser_config: Dict[str, Any]) -> None:
        parser_config[full_tag("startEvent")] = (SpiffStartEventParser, StartEvent)

    def start_delay_in_seconds(self, my_task: SpiffTask, now_in_utc: datetime) -> int:
        evaluated_expression = self.evaluated_timer_expression(my_task)

        if evaluated_expression is not None:
            if isinstance(self.timer_definition, TimeDateEventDefinition):
                parsed_duration = TimerEventDefinition.parse_time_or_duration(evaluated_expression)
                time_delta = parsed_duration - now_in_utc
                return time_delta.seconds  # type: ignore
            elif isinstance(self.timer_definition, DurationTimerEventDefinition):
                parsed_duration = TimerEventDefinition.parse_iso_duration(evaluated_expression)
                time_delta = TimerEventDefinition.get_timedelta_from_start(parsed_duration, now_in_utc)
                return time_delta.seconds  # type: ignore
            else:
                cycle_configuration = self.cycle_configuration(my_task, evaluated_expression)
                if cycle_configuration is not None:
                    _, start, _ = cycle_configuration
                    # TODO: hack to get this kicked over to the background processor since creating
                    # new instances per cycle need to happen there.
                    time_delta = start - now_in_utc + timedelta(seconds=10)
                    return time_delta.seconds  # type: ignore

        return 0

    def evaluated_timer_expression(self, my_task: SpiffTask) -> Any:
        script_engine = my_task.workflow.script_engine
        evaluated_expression = None
        parsed_duration = None

        if isinstance(self.timer_definition, TimerEventDefinition) and script_engine is not None:
            evaluated_expression = script_engine.evaluate(my_task, self.timer_definition.expression)
        return evaluated_expression

    def is_cycle_timer(self) -> bool:
        return isinstance(self.timer_definition, CycleTimerEventDefinition)

    def cycle_configuration(self, my_task: SpiffTask, evaluated_expression: Optional[Any] = None) -> Optional[Tuple[int, datetime, timedelta]]:
        if evaluated_expression is None:
            evaluated_expression = self.evaluated_timer_expression(my_task)

        if evaluated_expression is not None:
            if isinstance(self.timer_definition, CycleTimerEventDefinition):
                return TimerEventDefinition.parse_iso_recurring_interval(evaluated_expression)
        return None


class StartEventConverter(EventConverter):  # type: ignore
    def __init__(self, registry):  # type: ignore
        super().__init__(StartEvent, registry)

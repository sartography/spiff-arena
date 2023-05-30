from collections.abc import Generator
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pytest
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow  # type: ignore
from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore
from spiffworkflow_backend.services.workflow_service import WorkflowService
from spiffworkflow_backend.specs.start_event import StartEvent

from tests.spiffworkflow_backend.helpers.base_test import BaseTest

BPMN_WRAPPER = """
  <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
    xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
    id="Definitions_96f6665"
    targetNamespace="http://bpmn.io/schema/bpmn"
    exporter="Camunda Modeler"
    exporterVersion="3.0.0-dev"
  >
      {}
  </bpmn:definitions>
"""


@pytest.fixture()
def now_in_utc() -> Generator[datetime, None, None]:
    yield datetime.now(timezone.utc)


@pytest.fixture()
def example_start_datetime_in_utc_str() -> Generator[str, None, None]:
    yield "2019-10-01T12:00:00+00:00"


@pytest.fixture()
def example_start_datetime_minus_5_mins_in_utc(
    example_start_datetime_in_utc_str: str,
) -> Generator[datetime, None, None]:
    example_datetime = datetime.fromisoformat(example_start_datetime_in_utc_str)
    yield example_datetime - timedelta(minutes=5)


class CustomBpmnDmnParser(BpmnDmnParser):  # type: ignore
    OVERRIDE_PARSER_CLASSES = {}
    OVERRIDE_PARSER_CLASSES.update(BpmnDmnParser.OVERRIDE_PARSER_CLASSES)
    OVERRIDE_PARSER_CLASSES.update(SpiffBpmnParser.OVERRIDE_PARSER_CLASSES)

    StartEvent.register_parser_class(OVERRIDE_PARSER_CLASSES)


def workflow_from_str(bpmn_str: str, process_id: str) -> BpmnWorkflow:
    parser = CustomBpmnDmnParser()
    parser.add_bpmn_str(bpmn_str)
    top_level = parser.get_spec(process_id)
    subprocesses = parser.get_subprocess_specs(process_id)
    return BpmnWorkflow(top_level, subprocesses)


def workflow_from_fragment(bpmn_fragment: str, process_id: str) -> BpmnWorkflow:
    return workflow_from_str(BPMN_WRAPPER.format(bpmn_fragment), process_id)


class TestWorkflowService(BaseTest):
    """TestWorkflowService."""

    def test_run_at_delay_is_0_for_regular_start_events(self, now_in_utc: datetime) -> None:
        workflow = workflow_from_fragment(
            """
            <bpmn:process id="no_tasks" name="No Tasks" isExecutable="true">
              <bpmn:startEvent id="StartEvent_1">
                <bpmn:outgoing>Flow_184umot</bpmn:outgoing>
              </bpmn:startEvent>
              <bpmn:endEvent id="Event_0qq9il3">
                <bpmn:incoming>Flow_184umot</bpmn:incoming>
              </bpmn:endEvent>
              <bpmn:sequenceFlow id="Flow_184umot" sourceRef="StartEvent_1" targetRef="Event_0qq9il3" />
            </bpmn:process>
            """,
            "no_tasks",
        )
        _, delay, _ = WorkflowService.next_start_event_configuration(workflow, now_in_utc)  # type: ignore
        assert delay == 0

    def test_run_at_delay_is_30_for_30_second_duration_start_timer_event(self, now_in_utc: datetime) -> None:
        workflow = workflow_from_fragment(
            """
            <bpmn:process id="Process_aldvgey" isExecutable="true">
              <bpmn:startEvent id="StartEvent_1">
                <bpmn:outgoing>Flow_1x1o335</bpmn:outgoing>
                <bpmn:timerEventDefinition id="TimerEventDefinition_1vi6a54">
                  <bpmn:timeDuration xsi:type="bpmn:tFormalExpression">"PT30S"</bpmn:timeDuration>
                </bpmn:timerEventDefinition>
              </bpmn:startEvent>
              <bpmn:sequenceFlow id="Flow_1x1o335" sourceRef="StartEvent_1" targetRef="Event_0upbokh" />
              <bpmn:endEvent id="Event_0upbokh">
                <bpmn:incoming>Flow_1x1o335</bpmn:incoming>
              </bpmn:endEvent>
            </bpmn:process>
            """,
            "Process_aldvgey",
        )
        _, delay, _ = WorkflowService.next_start_event_configuration(workflow, now_in_utc)  # type: ignore
        assert delay == 30

    def test_run_at_delay_is_300_if_5_mins_before_date_start_timer_event(
        self, example_start_datetime_in_utc_str: str, example_start_datetime_minus_5_mins_in_utc: datetime
    ) -> None:
        workflow = workflow_from_fragment(
            f"""
            <bpmn:process id="Process_aldvgey" isExecutable="true">
              <bpmn:startEvent id="StartEvent_1">
                <bpmn:outgoing>Flow_1x1o335</bpmn:outgoing>
                <bpmn:timerEventDefinition id="TimerEventDefinition_1vi6a54">
                  <bpmn:timeDate xsi:type="bpmn:tFormalExpression">"{example_start_datetime_in_utc_str}"</bpmn:timeDate>
                </bpmn:timerEventDefinition>
              </bpmn:startEvent>
              <bpmn:sequenceFlow id="Flow_1x1o335" sourceRef="StartEvent_1" targetRef="Event_0upbokh" />
              <bpmn:endEvent id="Event_0upbokh">
                <bpmn:incoming>Flow_1x1o335</bpmn:incoming>
              </bpmn:endEvent>
            </bpmn:process>
            """,
            "Process_aldvgey",
        )
        _, delay, _ = WorkflowService.next_start_event_configuration(
            workflow, example_start_datetime_minus_5_mins_in_utc
        )  # type: ignore
        assert delay == 300

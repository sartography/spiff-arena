import json

from spiff_arena_common.runner import advance_workflow, specs_from_xml


MESSAGE_START_BPMN = (
    "message_start.bpmn",
    """
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  id="Definitions_message_start"
  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_message_start" isExecutable="true">
    <bpmn:startEvent id="Start_1" name="Check payment failed">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
      <bpmn:messageEventDefinition id="MessageEventDefinition_1" messageRef="Message_1" />
    </bpmn:startEvent>
    <bpmn:endEvent id="End_1">
      <bpmn:incoming>Flow_1</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="Start_1" targetRef="End_1" />
  </bpmn:process>
  <bpmn:message id="Message_1" name="check_payment_failed_request" />
</bpmn:definitions>
""",
)


def test_message_start_event_inherits_file_fixture_from_workflow(tmp_path):
    fixture_file = tmp_path / "recording.json"
    fixture_file.write_text(json.dumps({
        "pendingTaskStack": [
            {"id": "Start_1", "data": {"request": {}}},
        ],
    }))
    specs, error = specs_from_xml([MESSAGE_START_BPMN])
    assert error is None

    response = json.loads(advance_workflow(
        specs,
        {},
        None,
        "unittest",
        {"data": {"spiff_testFixture_file": str(fixture_file)}},
    ))

    assert response["completed"] is True
    assert response["result"]["request"] == {}

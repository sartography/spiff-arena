"""
Regression test: ReceiveTask must inherit workflow data from completed upstream tasks.

Bug: CustomReceiveTask._update_hook returned True without calling _inherit_data(),
so task.data was always {} when the ReceiveTask became READY.
"""
import json

from spiff_arena_common.runner import advance_workflow, specs_from_xml


receive_task_bpmn = ("receive_task_data.bpmn", """
<bpmn:definitions
  xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
  xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core"
  id="Definitions_receive_task_data"
  targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_receive_task_data" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:scriptTask id="SetX" name="Set x" scriptFormat="python">
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
      <bpmn:script>x = 42</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:scriptTask id="SetY" name="Set y" scriptFormat="python">
      <bpmn:incoming>Flow_2</bpmn:incoming>
      <bpmn:outgoing>Flow_3</bpmn:outgoing>
      <bpmn:script>y = "hello"</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:receiveTask id="ReceiveMsg" name="Receive Message" messageRef="Msg_1">
      <bpmn:incoming>Flow_3</bpmn:incoming>
      <bpmn:outgoing>Flow_4</bpmn:outgoing>
    </bpmn:receiveTask>
    <bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_4</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="SetX" />
    <bpmn:sequenceFlow id="Flow_2" sourceRef="SetX" targetRef="SetY" />
    <bpmn:sequenceFlow id="Flow_3" sourceRef="SetY" targetRef="ReceiveMsg" />
    <bpmn:sequenceFlow id="Flow_4" sourceRef="ReceiveMsg" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmn:message id="Msg_1" name="test_message" />
</bpmn:definitions>
""")


def test_receive_task_inherits_upstream_data():
    specs, err = specs_from_xml([receive_task_bpmn])
    assert err is None, err

    response = advance_workflow(specs, None, None, "greedy", {})
    response = json.loads(response) if isinstance(response, str) else response

    pending = response.get("pending_tasks", [])
    receive_tasks = [t for t in pending if t["task_spec"]["typename"] == "ReceiveTask"]
    assert receive_tasks, f"Expected a pending ReceiveTask, got: {[t['task_spec']['typename'] for t in pending]}"

    task_data = receive_tasks[0]["data"]
    assert task_data.get("x") == 42, f"Expected x=42 in task data, got: {task_data}"
    assert task_data.get("y") == "hello", f"Expected y='hello' in task data, got: {task_data}"

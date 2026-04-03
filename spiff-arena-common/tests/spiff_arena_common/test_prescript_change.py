import json

from spiff_arena_common.runner import advance_workflow, specs_from_xml


def make_bpmn(prescript):
    return ("prescript.bpmn", f"""
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="Activity_1" />
    <bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_2</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:userTask id="Activity_1" name="S1">
      <bpmn:extensionElements>
        <spiffworkflow:preScript>{prescript}</spiffworkflow:preScript>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_1</bpmn:incoming>
      <bpmn:outgoing>Flow_2</bpmn:outgoing>
    </bpmn:userTask>
    <bpmn:sequenceFlow id="Flow_2" sourceRef="Activity_1" targetRef="EndEvent_1" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1">
      <bpmndi:BPMNShape id="StartEvent_1_di" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="159" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_1_di" bpmnElement="Activity_1">
        <dc:Bounds x="270" y="137" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="432" y="159" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_1_di" bpmnElement="Flow_1">
        <di:waypoint x="215" y="177" />
        <di:waypoint x="270" y="177" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_2_di" bpmnElement="Flow_2">
        <di:waypoint x="370" y="177" />
        <di:waypoint x="432" y="177" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")


def find_task(step, bpmn_id):
    return [t for t in step["pending_tasks"] if t["task_spec"]["bpmn_id"] == bpmn_id][0]


def advance_until_task_ready(specs, bpmn_id):
    """Advance from fresh state until the given task is READY (16)."""
    step = json.loads(advance_workflow(specs, {}, None, "oneAtATime", None))
    assert step["status"] == "ok"

    # oneAtATime stops at each bpmn task; keep advancing until our target is READY
    for _ in range(10):
        tasks = [t for t in step.get("pending_tasks", [])
                 if t["task_spec"]["bpmn_id"] == bpmn_id and t["state"] == 16]
        if tasks:
            return step
        # Re-serialize state to match how the JS debugger passes it (via message passing)
        state = json.loads(json.dumps(step["state"]))
        step = json.loads(advance_workflow(specs, state, None, "oneAtATime", None))
        assert step["status"] == "ok"

    raise AssertionError(f"Task {bpmn_id} never reached READY state")


def test_prescript_change_uses_new_value_when_backed_up_to_future():
    """The fix: back up to where the task is FUTURE (not READY), so that
    re-advancing causes the READY transition which runs _update_hook (prescript).

    1. Parse BPMN with old pre-script, advance once (StartEvent READY, UserTask FUTURE)
    2. Re-parse BPMN with new pre-script
    3. Re-advance from the FUTURE state with new specs → predecessor runs,
       UserTask transitions to READY, _update_hook fires with new prescript
    """
    old_specs, err = specs_from_xml([make_bpmn('form_title = "Old Title"')])
    assert err is None

    # Step 1: first advance — StartEvent is READY, Activity_1 is FUTURE with clean data
    step1 = json.loads(advance_workflow(old_specs, {}, None, "oneAtATime", None))
    assert step1["status"] == "ok"

    # Verify Activity_1 is in FUTURE state (4) with no form_title
    future_task = [t for t in step1["state"]["tasks"].values()
                   if t["task_spec"] == "Activity_1"][0]
    assert future_task["state"] == 4  # FUTURE
    assert "form_title" not in future_task["data"]

    future_state_json = json.dumps(step1["state"])

    # Step 2: re-parse with new pre-script
    new_specs, err = specs_from_xml([make_bpmn('form_title = "New Title"')])
    assert err is None

    # Step 3: advance from FUTURE state with new specs.
    # StartEvent runs and completes, Activity_1 transitions to READY,
    # _update_hook fires with the new prescript setting form_title = "New Title"
    step2 = json.loads(advance_workflow(new_specs, json.loads(future_state_json), None, "oneAtATime", None))
    assert step2["status"] == "ok"

    user_task = find_task(step2, "Activity_1")
    assert user_task["state"] == 16  # READY — prescript ran during transition
    assert user_task["data"]["form_title"] == "New Title"


def test_prescript_change_NOT_reflected_when_backed_up_to_ready():
    """Documents the known limitation: if we back up only to READY state,
    the prescript does NOT re-run because _update_hook only fires during
    the READY transition, not on rehydration."""
    old_specs, err = specs_from_xml([make_bpmn('form_title = "Old Title"')])
    assert err is None

    step1 = advance_until_task_ready(old_specs, "Activity_1")
    user_task = find_task(step1, "Activity_1")
    assert user_task["state"] == 16

    ready_state_json = json.dumps(step1["state"])

    new_specs, err = specs_from_xml([make_bpmn('form_title = "New Title"')])
    assert err is None

    step2 = json.loads(advance_workflow(new_specs, json.loads(ready_state_json), None, "oneAtATime", None))
    assert step2["status"] == "ok"

    user_task2 = find_task(step2, "Activity_1")
    # BUG: prescript did NOT re-run — still has old value
    assert user_task2["data"]["form_title"] == "Old Title"

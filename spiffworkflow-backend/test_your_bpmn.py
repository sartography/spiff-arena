#!/usr/bin/env python3
"""Test script to run your original BPMN and see what tasks are created."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


def test_your_original_bpmn_with_diagnostics(
    app: Flask,
    client: FlaskClient,
    with_db_and_bpmn_file_cleanup: None,
) -> None:
    """Load your original BPMN and check for orphaned children."""

    # First, let me save your BPMN to the test data directory
    import os

    test_data_dir = "tests/data/orphaned_children_repro"
    os.makedirs(test_data_dir, exist_ok=True)

    # Your original BPMN content
    bpmn_content = """<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" targetNamespace="http://example.com/bpmn-builder">
  <bpmn:process id="Process_1" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_1</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:scriptTask id="ScriptTask_97071072" name="Initialize workflow state" scriptFormat="python">
  <bpmn:incoming>Flow_1</bpmn:incoming><bpmn:script>
# Initialize workflow state with workflow_id and timestamp
workflow_id = "wf-12345"
timestamp = "2024-01-15T10:00:00Z"
  </bpmn:script>
<bpmn:outgoing>Flow_1A2UzhVl</bpmn:outgoing></bpmn:scriptTask><bpmn:sequenceFlow id="Flow_1A2UzhVl" sourceRef="ScriptTask_97071072" targetRef="Gateway_Diverge_K47offUQ"/><bpmn:parallelGateway id="Gateway_Diverge_K47offUQ"><bpmn:incoming>Flow_1A2UzhVl</bpmn:incoming><bpmn:outgoing>Flow_Branch0_9bVEi2Qe</bpmn:outgoing><bpmn:outgoing>Flow_Branch1_FvQ4CAWq</bpmn:outgoing><bpmn:outgoing>Flow_Branch2_ZXfH2Wcs</bpmn:outgoing></bpmn:parallelGateway><bpmn:scriptTask id="ScriptTask_e4dbae96" name="Process data in branch A" scriptFormat="python">
  <bpmn:incoming>Flow_Branch0_9bVEi2Qe</bpmn:incoming><bpmn:script>
# Process data in branch A
# Set the branch A specific data
branch_a_data = "processed"
branch_a_status = "success"
  </bpmn:script>
<bpmn:outgoing>Flow_Vv5v6LKB</bpmn:outgoing></bpmn:scriptTask><bpmn:sequenceFlow id="Flow_Vv5v6LKB" sourceRef="ScriptTask_e4dbae96" targetRef="ScriptTask_88e12276"/><bpmn:scriptTask id="ScriptTask_88e12276" name="Complete branch A" scriptFormat="python">
  <bpmn:incoming>Flow_Vv5v6LKB</bpmn:incoming><bpmn:script>
# Complete branch A by updating the relevant status flags and adding branch-specific data
branch_a_completed = True
branch_a_data = "processed"
branch_a_status = "success"
  </bpmn:script>
<bpmn:outgoing>Flow_GQDWs8jp</bpmn:outgoing></bpmn:scriptTask><bpmn:sequenceFlow id="Flow_GQDWs8jp" sourceRef="ScriptTask_88e12276" targetRef="Gateway_Merge_24CSm5P7"/><bpmn:serviceTask xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="ServiceTask_vMbMJ2mK" name="Call external service that will fail">
  <bpmn:incoming>Flow_Branch1_FvQ4CAWq</bpmn:incoming><bpmn:extensionElements>
    <spiffworkflow:serviceTaskOperator id="http_PostRequestV2" resultVariable="api_response">http/PostRequestV2</spiffworkflow:serviceTaskOperator>
    <spiffworkflow:parameters>
      <spiffworkflow:parameter id="url" type="str" value="&quot;https://api.example.com/external-service&quot;"/>
      <spiffworkflow:parameter id="headers" type="any" value="{&quot;Content-Type&quot;: &quot;application/json&quot;}"/>
      <spiffworkflow:parameter id="data" type="any" value="{&quot;workflow_id&quot;: &quot;workflow_id&quot;, &quot;timestamp&quot;: &quot;timestamp&quot;}"/>
    </spiffworkflow:parameters>
    <spiffworkflow:postScript>
service_call_failed = True
service_response = {
    "error": api_response.get('body', {}).get('error', 'Unknown error'),
    "status_code": api_response.get('status_code', 500)
}
del api_response
    </spiffworkflow:postScript>
  </bpmn:extensionElements>
<bpmn:outgoing>Flow_F1wLwV7G</bpmn:outgoing></bpmn:serviceTask><bpmn:sequenceFlow id="Flow_F1wLwV7G" sourceRef="ServiceTask_vMbMJ2mK" targetRef="ScriptTask_dc236d4f"/><bpmn:scriptTask id="ScriptTask_dc236d4f" name="Handle service failure" scriptFormat="python">
  <bpmn:incoming>Flow_F1wLwV7G</bpmn:incoming><bpmn:script>
# Handle service failure by updating branch B status and logging the error
branch_b_completed = True
service_call_failed = True

# Create service response with error details
service_response = {
    "error": "Service unavailable",
    "status_code": 503
}

# Update branch B status to failed
branch_b_status = "failed"

# Log the error
error_logged = True
  </bpmn:script>
<bpmn:outgoing>Flow_aBGPDMRg</bpmn:outgoing></bpmn:scriptTask><bpmn:sequenceFlow id="Flow_aBGPDMRg" sourceRef="ScriptTask_dc236d4f" targetRef="Gateway_Merge_24CSm5P7"/><bpmn:scriptTask id="ScriptTask_a44e72a2" name="Perform validation checks" scriptFormat="python">
  <bpmn:incoming>Flow_Branch2_ZXfH2Wcs</bpmn:incoming><bpmn:script>
# Perform validation checks
# Count the number of completed branches (those with False value, meaning they haven't failed)
validation_count = 0

if not branch_a_completed:
    validation_count += 1
if not branch_b_completed:
    validation_count += 1
if not branch_c_completed:
    validation_count += 1

# Validation passes if all three branches are still in valid state (not failed)
# and service call hasn't failed, and workflow is started
validation_result = (
    workflow_started and
    not service_call_failed and
    validation_count == 3
)
  </bpmn:script>
<bpmn:outgoing>Flow_cTLiLqt5</bpmn:outgoing></bpmn:scriptTask><bpmn:sequenceFlow id="Flow_cTLiLqt5" sourceRef="ScriptTask_a44e72a2" targetRef="ScriptTask_7340737b"/><bpmn:scriptTask id="ScriptTask_7340737b" name="Complete branch C" scriptFormat="python">
  <bpmn:incoming>Flow_cTLiLqt5</bpmn:incoming><bpmn:script>
# Complete branch C by updating the relevant status variables
branch_c_completed = True
validation_result = True
validation_count = 3
branch_c_status = "success"
  </bpmn:script>
<bpmn:outgoing>Flow_OhDPk8iN</bpmn:outgoing></bpmn:scriptTask><bpmn:sequenceFlow id="Flow_OhDPk8iN" sourceRef="ScriptTask_7340737b" targetRef="Gateway_Merge_24CSm5P7"/><bpmn:parallelGateway id="Gateway_Merge_24CSm5P7"><bpmn:incoming>Flow_GQDWs8jp</bpmn:incoming><bpmn:incoming>Flow_aBGPDMRg</bpmn:incoming><bpmn:incoming>Flow_OhDPk8iN</bpmn:incoming><bpmn:outgoing>Flow_MergeToEnd_qaeGWTLv</bpmn:outgoing></bpmn:parallelGateway><bpmn:sequenceFlow id="Flow_MergeToEnd_qaeGWTLv" sourceRef="Gateway_Merge_24CSm5P7" targetRef="EndEvent_1"/><bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_MergeToEnd_qaeGWTLv</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_1" sourceRef="StartEvent_1" targetRef="ScriptTask_97071072"/>
  <bpmn:sequenceFlow id="Flow_Branch0_9bVEi2Qe" sourceRef="Gateway_Diverge_K47offUQ" targetRef="ScriptTask_e4dbae96" name="Branch A - Successful processing path"/><bpmn:sequenceFlow id="Flow_Branch1_FvQ4CAWq" sourceRef="Gateway_Diverge_K47offUQ" targetRef="ServiceTask_vMbMJ2mK" name="Branch B - Service task that fails immediately"/><bpmn:sequenceFlow id="Flow_Branch2_ZXfH2Wcs" sourceRef="Gateway_Diverge_K47offUQ" targetRef="ScriptTask_a44e72a2" name="Branch C - Another successful processing path"/></bpmn:process>
<ns0:BPMNDiagram xmlns:ns0="http://www.omg.org/spec/BPMN/20100524/DI" id="BPMNDiagram_Process_1"><ns0:BPMNPlane id="BPMNPlane_Process_1" bpmnElement="Process_1"><ns0:BPMNShape id="Shape_StartEvent_1" bpmnElement="StartEvent_1"><ns1:Bounds xmlns:ns1="http://www.omg.org/spec/DD/20100524/DC" x="100" y="222" width="36" height="36"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_ScriptTask_97071072" bpmnElement="ScriptTask_97071072"><ns2:Bounds xmlns:ns2="http://www.omg.org/spec/DD/20100524/DC" x="286" y="200" width="100" height="80"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_Gateway_Diverge_K47offUQ" bpmnElement="Gateway_Diverge_K47offUQ" isMarkerVisible="true"><ns3:Bounds xmlns:ns3="http://www.omg.org/spec/DD/20100524/DC" x="536" y="215" width="50" height="50"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_ScriptTask_e4dbae96" bpmnElement="ScriptTask_e4dbae96"><ns4:Bounds xmlns:ns4="http://www.omg.org/spec/DD/20100524/DC" x="736" y="100" width="100" height="80"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_ScriptTask_88e12276" bpmnElement="ScriptTask_88e12276"><ns5:Bounds xmlns:ns5="http://www.omg.org/spec/DD/20100524/DC" x="986" y="100" width="100" height="80"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_ServiceTask_vMbMJ2mK" bpmnElement="ServiceTask_vMbMJ2mK"><ns6:Bounds xmlns:ns6="http://www.omg.org/spec/DD/20100524/DC" x="1236" y="300" width="100" height="80"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_ScriptTask_dc236d4f" bpmnElement="ScriptTask_dc236d4f"><ns7:Bounds xmlns:ns7="http://www.omg.org/spec/DD/20100524/DC" x="1486" y="300" width="100" height="80"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_ScriptTask_a44e72a2" bpmnElement="ScriptTask_a44e72a2"><ns8:Bounds xmlns:ns8="http://www.omg.org/spec/DD/20100524/DC" x="1736" y="0" width="100" height="80"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_ScriptTask_7340737b" bpmnElement="ScriptTask_7340737b"><ns9:Bounds xmlns:ns9="http://www.omg.org/spec/DD/20100524/DC" x="1986" y="0" width="100" height="80"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_Gateway_Merge_24CSm5P7" bpmnElement="Gateway_Merge_24CSm5P7" isMarkerVisible="true"><ns10:Bounds xmlns:ns10="http://www.omg.org/spec/DD/20100524/DC" x="2236" y="215" width="50" height="50"/></ns0:BPMNShape><ns0:BPMNShape id="Shape_EndEvent_1" bpmnElement="EndEvent_1"><ns11:Bounds xmlns:ns11="http://www.omg.org/spec/DD/20100524/DC" x="2436" y="222" width="36" height="36"/></ns0:BPMNShape><ns0:BPMNEdge id="Edge_Flow_1A2UzhVl" bpmnElement="Flow_1A2UzhVl"><ns12:waypoint xmlns:ns12="http://www.omg.org/spec/DD/20100524/DI" x="386" y="240"/><ns13:waypoint xmlns:ns13="http://www.omg.org/spec/DD/20100524/DI" x="536" y="240"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_Vv5v6LKB" bpmnElement="Flow_Vv5v6LKB"><ns14:waypoint xmlns:ns14="http://www.omg.org/spec/DD/20100524/DI" x="836" y="140"/><ns15:waypoint xmlns:ns15="http://www.omg.org/spec/DD/20100524/DI" x="986" y="140"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_GQDWs8jp" bpmnElement="Flow_GQDWs8jp"><ns16:waypoint xmlns:ns16="http://www.omg.org/spec/DD/20100524/DI" x="1086" y="140"/><ns17:waypoint xmlns:ns17="http://www.omg.org/spec/DD/20100524/DI" x="1661" y="140"/><ns18:waypoint xmlns:ns18="http://www.omg.org/spec/DD/20100524/DI" x="1661" y="240"/><ns19:waypoint xmlns:ns19="http://www.omg.org/spec/DD/20100524/DI" x="2236" y="240"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_F1wLwV7G" bpmnElement="Flow_F1wLwV7G"><ns20:waypoint xmlns:ns20="http://www.omg.org/spec/DD/20100524/DI" x="1336" y="340"/><ns21:waypoint xmlns:ns21="http://www.omg.org/spec/DD/20100524/DI" x="1486" y="340"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_aBGPDMRg" bpmnElement="Flow_aBGPDMRg"><ns22:waypoint xmlns:ns22="http://www.omg.org/spec/DD/20100524/DI" x="1586" y="340"/><ns23:waypoint xmlns:ns23="http://www.omg.org/spec/DD/20100524/DI" x="1911" y="340"/><ns24:waypoint xmlns:ns24="http://www.omg.org/spec/DD/20100524/DI" x="1911" y="240"/><ns25:waypoint xmlns:ns25="http://www.omg.org/spec/DD/20100524/DI" x="2236" y="240"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_cTLiLqt5" bpmnElement="Flow_cTLiLqt5"><ns26:waypoint xmlns:ns26="http://www.omg.org/spec/DD/20100524/DI" x="1836" y="40"/><ns27:waypoint xmlns:ns27="http://www.omg.org/spec/DD/20100524/DI" x="1986" y="40"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_OhDPk8iN" bpmnElement="Flow_OhDPk8iN"><ns28:waypoint xmlns:ns28="http://www.omg.org/spec/DD/20100524/DI" x="2086" y="40"/><ns29:waypoint xmlns:ns29="http://www.omg.org/spec/DD/20100524/DI" x="2161" y="40"/><ns30:waypoint xmlns:ns30="http://www.omg.org/spec/DD/20100524/DI" x="2161" y="240"/><ns31:waypoint xmlns:ns31="http://www.omg.org/spec/DD/20100524/DI" x="2236" y="240"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_MergeToEnd_qaeGWTLv" bpmnElement="Flow_MergeToEnd_qaeGWTLv"><ns32:waypoint xmlns:ns32="http://www.omg.org/spec/DD/20100524/DI" x="2286" y="240"/><ns33:waypoint xmlns:ns33="http://www.omg.org/spec/DD/20100524/DI" x="2436" y="240"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_1" bpmnElement="Flow_1"><ns34:waypoint xmlns:ns34="http://www.omg.org/spec/DD/20100524/DI" x="136" y="240"/><ns35:waypoint xmlns:ns35="http://www.omg.org/spec/DD/20100524/DI" x="286" y="240"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_Branch0_9bVEi2Qe" bpmnElement="Flow_Branch0_9bVEi2Qe"><ns36:waypoint xmlns:ns36="http://www.omg.org/spec/DD/20100524/DI" x="586" y="240"/><ns37:waypoint xmlns:ns37="http://www.omg.org/spec/DD/20100524/DI" x="661" y="240"/><ns38:waypoint xmlns:ns38="http://www.omg.org/spec/DD/20100524/DI" x="661" y="140"/><ns39:waypoint xmlns:ns39="http://www.omg.org/spec/DD/20100524/DI" x="736" y="140"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_Branch1_FvQ4CAWq" bpmnElement="Flow_Branch1_FvQ4CAWq"><ns40:waypoint xmlns:ns40="http://www.omg.org/spec/DD/20100524/DI" x="586" y="240"/><ns41:waypoint xmlns:ns41="http://www.omg.org/spec/DD/20100524/DI" x="911" y="240"/><ns42:waypoint xmlns:ns42="http://www.omg.org/spec/DD/20100524/DI" x="911" y="340"/><ns43:waypoint xmlns:ns43="http://www.omg.org/spec/DD/20100524/DI" x="1236" y="340"/></ns0:BPMNEdge><ns0:BPMNEdge id="Edge_Flow_Branch2_ZXfH2Wcs" bpmnElement="Flow_Branch2_ZXfH2Wcs"><ns44:waypoint xmlns:ns44="http://www.omg.org/spec/DD/20100524/DI" x="586" y="240"/><ns45:waypoint xmlns:ns45="http://www.omg.org/spec/DD/20100524/DI" x="1161" y="240"/><ns46:waypoint xmlns:ns46="http://www.omg.org/spec/DD/20100524/DI" x="1161" y="40"/><ns47:waypoint xmlns:ns47="http://www.omg.org/spec/DD/20100524/DI" x="1736" y="40"/></ns0:BPMNEdge></ns0:BPMNPlane></ns0:BPMNDiagram></bpmn:definitions>"""

    with open(f"{test_data_dir}/user_original.bpmn", "w") as f:
        f.write(bpmn_content)

    base_test = BaseTest()

    process_model = load_test_spec(
        process_model_id="test/user_original",
        bpmn_file_name="user_original.bpmn",
        process_model_source_directory="orphaned_children_repro",
    )

    process_instance = base_test.create_process_instance_from_process_model(process_model=process_model)

    processor = ProcessInstanceProcessor(process_instance)

    # Run and expect failure
    try:
        processor.do_engine_steps(save=True)
        print("⚠️  Process completed without error (unexpected)")
    except WorkflowExecutionServiceError as e:
        print(f"✓ Process failed as expected: {str(e)[:100]}...")

    # Refresh and check
    db.session.refresh(process_instance)

    all_tasks = TaskModel.query.filter_by(process_instance_id=process_instance.id).all()

    existing_guids = {t.guid for t in all_tasks}

    print(f"\n{'=' * 80}")
    print("TASK ANALYSIS FOR USER'S ORIGINAL BPMN")
    print(f"{'=' * 80}")
    print(f"\nTotal tasks: {len(all_tasks)}")

    # Count by state
    by_state = {}
    for task in all_tasks:
        by_state[task.state] = by_state.get(task.state, 0) + 1
    print("\nTasks by state:")
    for state, count in sorted(by_state.items()):
        print(f"  {state}: {count}")

    # Check for orphaned children
    orphaned_found = False
    for task in all_tasks:
        if "children" not in task.properties_json:
            continue

        children = task.properties_json["children"]
        if not children:
            continue

        task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"

        missing = [c for c in children if c not in existing_guids]
        if missing:
            orphaned_found = True
            print("\n🐛 ORPHANED CHILDREN FOUND!")
            print(f"  Parent: {task_def} [{task.state}]")
            print(f"  GUID: {task.guid}")
            print(f"  Children in JSON: {len(children)}")
            print(f"  Missing: {len(missing)}")
            for m in missing:
                print(f"    ✗ {m}")

    if not orphaned_found:
        print("\n✅ No orphaned children found")
        print("Your BPMN didn't reproduce the bug in this test environment")

    # Print full task tree
    print(f"\n{'=' * 80}")
    print("FULL TASK TREE")
    print(f"{'=' * 80}")
    for task in all_tasks:
        task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"
        children = task.properties_json.get("children", [])
        print(f"\n{task_def} [{task.state}]")
        print(f"  GUID: {task.guid[:16]}...")
        if children:
            print(f"  Children: {len(children)}")
            for child_guid in children:
                exists = "✓" if child_guid in existing_guids else "✗ MISSING"
                print(f"    {exists} {child_guid[:16]}...")


if __name__ == "__main__":
    import sys

    sys.exit(pytest.main([__file__, "-xvs"]))

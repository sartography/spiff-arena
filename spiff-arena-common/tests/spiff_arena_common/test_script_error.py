import json
import pytest

from spiff_arena_common.runner import advance_workflow, specs_from_xml

err_line_2 = ("script_error2.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_script_error_n1k45pt" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_17db3yp</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_17db3yp" sourceRef="StartEvent_1" targetRef="Activity_0qpzdpu" />
    <bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_12pkbxb</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_12pkbxb" sourceRef="Activity_0qpzdpu" targetRef="EndEvent_1" />
    <bpmn:scriptTask id="Activity_0qpzdpu" name="Script with error">
      <bpmn:extensionElements>
        <spiffworkflow:instructionsForEndUser />
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_17db3yp</bpmn:incoming>
      <bpmn:outgoing>Flow_12pkbxb</bpmn:outgoing>
      <bpmn:script>True
3 in 5</bpmn:script>
    </bpmn:scriptTask>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_script_error_n1k45pt">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="159" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Event_14za570_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="432" y="159" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_0ikznwq_di" bpmnElement="Activity_0qpzdpu">
        <dc:Bounds x="270" y="137" width="100" height="80" />
        <bpmndi:BPMNLabel />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_17db3yp_di" bpmnElement="Flow_17db3yp">
        <di:waypoint x="215" y="177" />
        <di:waypoint x="270" y="177" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_12pkbxb_di" bpmnElement="Flow_12pkbxb">
        <di:waypoint x="370" y="177" />
        <di:waypoint x="432" y="177" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")

err_line_3 = ("script_error3.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_script_error_n1k45pt" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_17db3yp</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_17db3yp" sourceRef="StartEvent_1" targetRef="Activity_0qpzdpu" />
    <bpmn:endEvent id="EndEvent_1">
      <bpmn:incoming>Flow_12pkbxb</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_12pkbxb" sourceRef="Activity_0qpzdpu" targetRef="EndEvent_1" />
    <bpmn:scriptTask id="Activity_0qpzdpu" name="Script with error">
      <bpmn:extensionElements>
        <spiffworkflow:instructionsForEndUser />
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_17db3yp</bpmn:incoming>
      <bpmn:outgoing>Flow_12pkbxb</bpmn:outgoing>
      <bpmn:script>x = 1
y = 2
z = bob</bpmn:script>
    </bpmn:scriptTask>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_script_error_n1k45pt">
      <bpmndi:BPMNShape id="_BPMNShape_StartEvent_2" bpmnElement="StartEvent_1">
        <dc:Bounds x="179" y="159" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Event_14za570_di" bpmnElement="EndEvent_1">
        <dc:Bounds x="432" y="159" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_0ikznwq_di" bpmnElement="Activity_0qpzdpu">
        <dc:Bounds x="270" y="137" width="100" height="80" />
        <bpmndi:BPMNLabel />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow_17db3yp_di" bpmnElement="Flow_17db3yp">
        <di:waypoint x="215" y="177" />
        <di:waypoint x="270" y="177" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_12pkbxb_di" bpmnElement="Flow_12pkbxb">
        <di:waypoint x="370" y="177" />
        <di:waypoint x="432" y="177" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")

@pytest.mark.parametrize(
    "file,line_number,error_line",
    [
        (err_line_2, 2, "3 in 5"),
        (err_line_3, 3, "z = bob"),
    ]
)
def test_script_error(file, line_number, error_line):
    specs, err = specs_from_xml([file])
    assert err is None
    
    result = json.loads(advance_workflow(specs, {}, None, "greedy", None))
    assert result["status"] == "error"
    assert result["line_number"] == line_number
    assert result["error_line"] == error_line

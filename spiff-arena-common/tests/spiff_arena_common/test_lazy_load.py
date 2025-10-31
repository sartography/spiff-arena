import json
import pytest

from spiff_arena_common.runner import advance_workflow, specs_from_xml

ca_host = ("ca_host.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_1761747779744" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1761747779744">
      <bpmn:outgoing>Flow1_1761747779744</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_1761747779744">
      <bpmn:incoming>Flow2_1761747779744</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow1_1761747779744" sourceRef="StartEvent_1761747779744" targetRef="Task_1761747779744" />
    <bpmn:sequenceFlow id="Flow2_1761747779744" sourceRef="Task_1761747779744" targetRef="EndEvent_1761747779744" />
    <bpmn:callActivity id="Task_1761747779744" calledElement="Process_1761319842685">
      <bpmn:incoming>Flow1_1761747779744</bpmn:incoming>
      <bpmn:outgoing>Flow2_1761747779744</bpmn:outgoing>
    </bpmn:callActivity>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1761747779744">
      <bpmndi:BPMNShape id="StartEvent_1761747779744_di" bpmnElement="StartEvent_1761747779744">
        <dc:Bounds x="182" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1761747779744_di" bpmnElement="EndEvent_1761747779744">
        <dc:Bounds x="402" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_1i80fn4_di" bpmnElement="Task_1761747779744">
        <dc:Bounds x="260" y="120" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow1_1761747779744_di" bpmnElement="Flow1_1761747779744">
        <di:waypoint x="218" y="160" />
        <di:waypoint x="260" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow2_1761747779744_di" bpmnElement="Flow2_1761747779744">
        <di:waypoint x="360" y="160" />
        <di:waypoint x="402" y="160" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")

ca_host_mi_seq = ("ca_host_mi_seq.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_1761747779744" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1761747779744">
      <bpmn:outgoing>Flow1_1761747779744</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_1761747779744">
      <bpmn:incoming>Flow_0x8yq1j</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow1_1761747779744" sourceRef="StartEvent_1761747779744" targetRef="Task_1761747779744" />
    <bpmn:sequenceFlow id="Flow2_1761747779744" sourceRef="Task_1761747779744" targetRef="Activity_07197h0" />
    <bpmn:callActivity id="Task_1761747779744" calledElement="Process_1761319842685">
      <bpmn:incoming>Flow1_1761747779744</bpmn:incoming>
      <bpmn:outgoing>Flow2_1761747779744</bpmn:outgoing>
      <bpmn:multiInstanceLoopCharacteristics isSequential="true">
        <bpmn:loopCardinality xsi:type="bpmn:tFormalExpression">1</bpmn:loopCardinality>
      </bpmn:multiInstanceLoopCharacteristics>
    </bpmn:callActivity>
    <bpmn:sequenceFlow id="Flow_0x8yq1j" sourceRef="Activity_07197h0" targetRef="EndEvent_1761747779744" />
    <bpmn:scriptTask id="Activity_07197h0">
      <bpmn:incoming>Flow2_1761747779744</bpmn:incoming>
      <bpmn:outgoing>Flow_0x8yq1j</bpmn:outgoing>
      <bpmn:multiInstanceLoopCharacteristics>
        <bpmn:loopCardinality xsi:type="bpmn:tFormalExpression">1</bpmn:loopCardinality>
      </bpmn:multiInstanceLoopCharacteristics>
      <bpmn:script>x = 1</bpmn:script>
    </bpmn:scriptTask>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1761747779744">
      <bpmndi:BPMNShape id="StartEvent_1761747779744_di" bpmnElement="StartEvent_1761747779744">
        <dc:Bounds x="182" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_1i80fn4_di" bpmnElement="Task_1761747779744">
        <dc:Bounds x="260" y="120" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1761747779744_di" bpmnElement="EndEvent_1761747779744">
        <dc:Bounds x="542" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_0fpmktw_di" bpmnElement="Activity_07197h0">
        <dc:Bounds x="400" y="120" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow1_1761747779744_di" bpmnElement="Flow1_1761747779744">
        <di:waypoint x="218" y="160" />
        <di:waypoint x="260" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow2_1761747779744_di" bpmnElement="Flow2_1761747779744">
        <di:waypoint x="360" y="160" />
        <di:waypoint x="400" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_0x8yq1j_di" bpmnElement="Flow_0x8yq1j">
        <di:waypoint x="500" y="160" />
        <di:waypoint x="542" y="160" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")

@pytest.mark.parametrize(
    "files,expected",
    [
        ([ca_host], ["Process_1761319842685"]),
        ([ca_host_mi_seq], ["Process_1761319842685"]),
    ]
)
def test_lazy_load(files, expected):
    specs, err = specs_from_xml(files)
    assert err is None
    
    result = json.loads(advance_workflow(specs, {}, None, "oneAtATime", None))
    assert result.get("error") is None
    assert not result["completed"]
    
    lazy_loads = result["lazy_loads"]
    assert lazy_loads == expected

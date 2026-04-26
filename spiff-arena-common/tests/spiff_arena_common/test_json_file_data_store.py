import json
import pytest

from spiff_arena_common.data_stores import JSONFileDataStore, JSONFileDataStoreConverter

from SpiffWorkflow.spiff.serializer.config import SPIFF_CONFIG


disk = { "jsonfiledatastore.json": {} }

class JSONFileDataStoreDelegate:
    def get(self, bpmn_id, my_task):
        data = disk[f"{bpmn_id}.json"]
        return data, None
    def set(self, bpmn_id, my_task, data):
        disk[f"{bpmn_id}.json"] = data
        return None

class MyJSONFileDataStoreConverter(JSONFileDataStoreConverter):
    def from_dict(self, dct):
        ds = super().from_dict(dct)
        ds.delegate = JSONFileDataStoreDelegate()
        return ds

SPIFF_CONFIG[JSONFileDataStore] = MyJSONFileDataStoreConverter

from spiff_arena_common.runner import advance_workflow, specs_from_xml  # noqa: E402

jfds = ("jfds.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_1772027573278" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1772027573278">
      <bpmn:outgoing>Flow1_1772027573278</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_1772027573278">
      <bpmn:incoming>Flow_1qufhs6</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow1_1772027573278" sourceRef="StartEvent_1772027573278" targetRef="Task_1772027573278" />
    <bpmn:sequenceFlow id="Flow2_1772027573278" sourceRef="Task_1772027573278" targetRef="Activity_1sqqjix" />
    <bpmn:scriptTask id="Task_1772027573278">
      <bpmn:incoming>Flow1_1772027573278</bpmn:incoming>
      <bpmn:outgoing>Flow2_1772027573278</bpmn:outgoing>
      <bpmn:property id="Property_0omgjkt" name="__targetRef_placeholder" />
      <bpmn:dataInputAssociation id="DataInputAssociation_0ff9dat">
        <bpmn:sourceRef>DataStoreReference_0kann3y</bpmn:sourceRef>
        <bpmn:targetRef>Property_0omgjkt</bpmn:targetRef>
      </bpmn:dataInputAssociation>
      <bpmn:script>x = jsonfiledatastore.get("x", 1)</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:dataStoreReference id="DataStoreReference_0kann3y" name="jsonfiledatastore" dataStoreRef="jsonfiledatastore" type="jsonfile" />
    <bpmn:sequenceFlow id="Flow_1qufhs6" sourceRef="Activity_1sqqjix" targetRef="EndEvent_1772027573278" />
    <bpmn:scriptTask id="Activity_1sqqjix">
      <bpmn:incoming>Flow2_1772027573278</bpmn:incoming>
      <bpmn:outgoing>Flow_1qufhs6</bpmn:outgoing>
      <bpmn:dataOutputAssociation id="DataOutputAssociation_1he6cu4">
        <bpmn:targetRef>DataStoreReference_0wm2yyl</bpmn:targetRef>
      </bpmn:dataOutputAssociation>
      <bpmn:script>jsonfiledatastore = {
  "x": x + 1
}</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:dataStoreReference id="DataStoreReference_0wm2yyl" name="jsonfiledatastore" dataStoreRef="jsonfiledatastore" type="jsonfile" />
  </bpmn:process>
  <bpmn:dataStore id="jsonfiledatastore" name="JSONFileDataStore" />
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1772027573278">
      <bpmndi:BPMNShape id="StartEvent_1772027573278_di" bpmnElement="StartEvent_1772027573278">
        <dc:Bounds x="182" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_0nnityz_di" bpmnElement="Task_1772027573278">
        <dc:Bounds x="260" y="120" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="DataStoreReference_0kann3y_di" bpmnElement="DataStoreReference_0kann3y">
        <dc:Bounds x="245" y="275" width="50" height="50" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="228" y="332" width="85" height="27" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1772027573278_di" bpmnElement="EndEvent_1772027573278">
        <dc:Bounds x="562" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_1f3om85_di" bpmnElement="Activity_1sqqjix">
        <dc:Bounds x="400" y="120" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="DataStoreReference_0wm2yyl_di" bpmnElement="DataStoreReference_0wm2yyl">
        <dc:Bounds x="435" y="275" width="50" height="50" />
        <bpmndi:BPMNLabel>
          <dc:Bounds x="418" y="332" width="85" height="27" />
        </bpmndi:BPMNLabel>
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow1_1772027573278_di" bpmnElement="Flow1_1772027573278">
        <di:waypoint x="218" y="160" />
        <di:waypoint x="260" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow2_1772027573278_di" bpmnElement="Flow2_1772027573278">
        <di:waypoint x="360" y="160" />
        <di:waypoint x="400" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="DataInputAssociation_0ff9dat_di" bpmnElement="DataInputAssociation_0ff9dat">
        <di:waypoint x="279" y="275" />
        <di:waypoint x="306" y="200" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_1qufhs6_di" bpmnElement="Flow_1qufhs6">
        <di:waypoint x="500" y="160" />
        <di:waypoint x="562" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="DataOutputAssociation_1he6cu4_di" bpmnElement="DataOutputAssociation_1he6cu4">
        <di:waypoint x="453" y="200" />
        <di:waypoint x="459" y="275" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")

@pytest.mark.parametrize(
    "file,expected",
    [
        (jfds, 1),
        (jfds, 2),
        (jfds, 3),
    ]
)
def test_json_file_data_store(file, expected):
    specs, err = specs_from_xml([file])
    assert err is None
    
    result = json.loads(advance_workflow(specs, {}, None, "greedy", None))
    assert result.get("error") is None
    assert result["completed"]
    assert result["status"] == "ok"
    assert result["result"]["x"] == expected

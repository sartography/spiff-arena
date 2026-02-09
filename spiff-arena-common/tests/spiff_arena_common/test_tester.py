import json
import pytest

from spiff_arena_common.runner import specs_from_xml
from spiff_arena_common.tester import run_tests

ut = ("ut.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_1770128055928" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1770128055928">
      <bpmn:outgoing>Flow1_1770128055928</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_1770128055928">
      <bpmn:incoming>Flow_1437bw5</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow1_1770128055928" sourceRef="StartEvent_1770128055928" targetRef="ut_task" />
    <bpmn:userTask id="ut_task">
      <bpmn:extensionElements>
        <spiffworkflow:properties>
          <spiffworkflow:property name="formJsonSchemaFilename" value="ut-schema.json" />
          <spiffworkflow:property name="formUiSchemaFilename" value="ut-uischema.json" />
        </spiffworkflow:properties>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow1_1770128055928</bpmn:incoming>
      <bpmn:outgoing>Flow_1437bw5</bpmn:outgoing>
    </bpmn:userTask>
    <bpmn:sequenceFlow id="Flow_1437bw5" sourceRef="ut_task" targetRef="EndEvent_1770128055928" />
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1770128055928">
      <bpmndi:BPMNShape id="StartEvent_1770128055928_di" bpmnElement="StartEvent_1770128055928">
        <dc:Bounds x="182" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_0523rce_di" bpmnElement="ut_task">
        <dc:Bounds x="260" y="120" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1770128055928_di" bpmnElement="EndEvent_1770128055928">
        <dc:Bounds x="412" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow1_1770128055928_di" bpmnElement="Flow1_1770128055928">
        <di:waypoint x="218" y="160" />
        <di:waypoint x="260" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_1437bw5_di" bpmnElement="Flow_1437bw5">
        <di:waypoint x="360" y="160" />
        <di:waypoint x="412" y="160" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")

ut_test = ("ut_test.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" xmlns:dc="http://www.omg.org/spec/DD/20100524/DC" xmlns:di="http://www.omg.org/spec/DD/20100524/DI" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="Definitions_96f6665" targetNamespace="http://bpmn.io/schema/bpmn" exporter="Camunda Modeler" exporterVersion="3.0.0-dev">
  <bpmn:process id="Process_1770132558798" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1770132558798">
      <bpmn:outgoing>Flow1_1770132558798</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:endEvent id="EndEvent_1770132558798">
      <bpmn:incoming>Flow_1bhqy5q</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow1_1770132558798" sourceRef="StartEvent_1770132558798" targetRef="Activity_0d27dhn" />
    <bpmn:sequenceFlow id="Flow2_1770132558798" sourceRef="Task_1770132558798" targetRef="Activity_0f6vlzg" />
    <bpmn:callActivity id="Task_1770132558798" name="Run ut" calledElement="Process_1770128055928">
      <bpmn:incoming>Flow_1fbs4ll</bpmn:incoming>
      <bpmn:outgoing>Flow2_1770132558798</bpmn:outgoing>
    </bpmn:callActivity>
    <bpmn:sequenceFlow id="Flow_1a46c5r" sourceRef="Activity_0f6vlzg" targetRef="Gateway_1gvxdru" />
    <bpmn:scriptTask id="Activity_0f6vlzg" name="Test Result">
      <bpmn:incoming>Flow2_1770132558798</bpmn:incoming>
      <bpmn:outgoing>Flow_1a46c5r</bpmn:outgoing>
      <bpmn:script>def runTests(tests):
  import io
  import unittest

  suite = unittest.TestSuite()
  suite.addTests(tests)
  stream = io.StringIO()
  result = unittest.TextTestRunner(stream=stream).run(suite)
  
  return {
    "testsRun": result.testsRun,
    "wasSuccessful": result.wasSuccessful(),
    "output": stream.getvalue(),
  }

def test():
  import unittest

  class TestTaskData(unittest.TestCase):
    def runTest(self):
      self.assertEqual(some_field, spiff_testFixture["expected"]["some_field"])
      
  return runTests([TestTaskData()])
  
spiff_testResult = test()</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:exclusiveGateway id="Gateway_1gvxdru" default="Flow_00tp9fz">
      <bpmn:incoming>Flow_1a46c5r</bpmn:incoming>
      <bpmn:outgoing>Flow_1m91fjn</bpmn:outgoing>
      <bpmn:outgoing>Flow_00tp9fz</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    <bpmn:sequenceFlow id="Flow_1m91fjn" sourceRef="Gateway_1gvxdru" targetRef="Gateway_1izg0qj">
      <bpmn:conditionExpression>spiff_testResult["wasSuccessful"]</bpmn:conditionExpression>
    </bpmn:sequenceFlow>
    <bpmn:exclusiveGateway id="Gateway_1izg0qj">
      <bpmn:incoming>Flow_1m91fjn</bpmn:incoming>
      <bpmn:incoming>Flow_0lmdtk5</bpmn:incoming>
      <bpmn:outgoing>Flow_1bhqy5q</bpmn:outgoing>
    </bpmn:exclusiveGateway>
    <bpmn:sequenceFlow id="Flow_1bhqy5q" sourceRef="Gateway_1izg0qj" targetRef="EndEvent_1770132558798" />
    <bpmn:sequenceFlow id="Flow_00tp9fz" sourceRef="Gateway_1gvxdru" targetRef="Activity_0mg5d2b" />
    <bpmn:sequenceFlow id="Flow_0lmdtk5" sourceRef="Activity_0mg5d2b" targetRef="Gateway_1izg0qj" />
    <bpmn:manualTask id="Activity_0mg5d2b">
      <bpmn:extensionElements>
        <spiffworkflow:instructionsForEndUser>{{ spiff_testResult["output"] }}</spiffworkflow:instructionsForEndUser>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_00tp9fz</bpmn:incoming>
      <bpmn:outgoing>Flow_0lmdtk5</bpmn:outgoing>
    </bpmn:manualTask>
    <bpmn:sequenceFlow id="Flow_1fbs4ll" sourceRef="Activity_0d27dhn" targetRef="Task_1770132558798" />
    <bpmn:scriptTask id="Activity_0d27dhn" name="Load Test Fixture">
      <bpmn:incoming>Flow1_1770132558798</bpmn:incoming>
      <bpmn:outgoing>Flow_1fbs4ll</bpmn:outgoing>
      <bpmn:script>spiff_testFixture = {
  "pendingTaskStack": [
    { "id": "ut_task", "data": { "some_field": "jj" } },
  ],
  "expected": {
    "some_field": "jj",
  }
}</bpmn:script>
    </bpmn:scriptTask>
  </bpmn:process>
  <bpmndi:BPMNDiagram id="BPMNDiagram_1">
    <bpmndi:BPMNPlane id="BPMNPlane_1" bpmnElement="Process_1770132558798">
      <bpmndi:BPMNShape id="StartEvent_1770132558798_di" bpmnElement="StartEvent_1770132558798">
        <dc:Bounds x="32" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="EndEvent_1770132558798_di" bpmnElement="EndEvent_1770132558798">
        <dc:Bounds x="802" y="142" width="36" height="36" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_00kzkju_di" bpmnElement="Task_1770132558798">
        <dc:Bounds x="260" y="120" width="100" height="80" />
        <bpmndi:BPMNLabel />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_0j88phz_di" bpmnElement="Activity_0f6vlzg">
        <dc:Bounds x="400" y="120" width="100" height="80" />
        <bpmndi:BPMNLabel />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_1gvxdru_di" bpmnElement="Gateway_1gvxdru" isMarkerVisible="true">
        <dc:Bounds x="525" y="135" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Gateway_1izg0qj_di" bpmnElement="Gateway_1izg0qj" isMarkerVisible="true">
        <dc:Bounds x="715" y="135" width="50" height="50" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_11mpvf0_di" bpmnElement="Activity_0mg5d2b">
        <dc:Bounds x="600" y="210" width="100" height="80" />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNShape id="Activity_0l1t70p_di" bpmnElement="Activity_0d27dhn">
        <dc:Bounds x="120" y="120" width="100" height="80" />
        <bpmndi:BPMNLabel />
      </bpmndi:BPMNShape>
      <bpmndi:BPMNEdge id="Flow1_1770132558798_di" bpmnElement="Flow1_1770132558798">
        <di:waypoint x="68" y="160" />
        <di:waypoint x="120" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow2_1770132558798_di" bpmnElement="Flow2_1770132558798">
        <di:waypoint x="360" y="160" />
        <di:waypoint x="400" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_1a46c5r_di" bpmnElement="Flow_1a46c5r">
        <di:waypoint x="500" y="160" />
        <di:waypoint x="525" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_1m91fjn_di" bpmnElement="Flow_1m91fjn">
        <di:waypoint x="575" y="160" />
        <di:waypoint x="715" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_1bhqy5q_di" bpmnElement="Flow_1bhqy5q">
        <di:waypoint x="765" y="160" />
        <di:waypoint x="802" y="160" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_00tp9fz_di" bpmnElement="Flow_00tp9fz">
        <di:waypoint x="550" y="185" />
        <di:waypoint x="550" y="250" />
        <di:waypoint x="600" y="250" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_0lmdtk5_di" bpmnElement="Flow_0lmdtk5">
        <di:waypoint x="700" y="250" />
        <di:waypoint x="740" y="250" />
        <di:waypoint x="740" y="185" />
      </bpmndi:BPMNEdge>
      <bpmndi:BPMNEdge id="Flow_1fbs4ll_di" bpmnElement="Flow_1fbs4ll">
        <di:waypoint x="220" y="160" />
        <di:waypoint x="260" y="160" />
      </bpmndi:BPMNEdge>
    </bpmndi:BPMNPlane>
  </bpmndi:BPMNDiagram>
</bpmn:definitions>
""")

@pytest.mark.parametrize(
    "files",
    [
        ([ut, ut_test]),
    ]
)
def test_tester(files):
    parsed = []
    for file in files:
        specs, err = specs_from_xml([file])
        assert err is None
        parsed.append((file[0], specs))
    [ctx, result, output] = run_tests(parsed)

    assert result.wasSuccessful()
    assert result.testsRun == 1
    assert output

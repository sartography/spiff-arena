import json
import pytest

from SpiffWorkflow.bpmn.specs.mixins.multiinstance_task import LoopTask
from SpiffWorkflow.spiff.specs.defaults import CallActivity
from SpiffWorkflow.util.task import TaskFilter, TaskState

from spiff_arena_common import runner
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


_BPMN = 'xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"'

looping_host = ("looping_host.bpmn", f"""
<bpmn:definitions {_BPMN} id="looping_host" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="LoopingHost" isExecutable="true">
    <bpmn:startEvent id="HostStart"><bpmn:outgoing>f1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:scriptTask id="Init"><bpmn:incoming>f1</bpmn:incoming><bpmn:outgoing>f2</bpmn:outgoing><bpmn:script>i = 0</bpmn:script></bpmn:scriptTask>
    <bpmn:exclusiveGateway id="Join"><bpmn:incoming>f2</bpmn:incoming><bpmn:incoming>f6</bpmn:incoming><bpmn:outgoing>f3</bpmn:outgoing></bpmn:exclusiveGateway>
    <bpmn:callActivity id="Call" calledElement="LoopingChild"><bpmn:incoming>f3</bpmn:incoming><bpmn:outgoing>f4</bpmn:outgoing></bpmn:callActivity>
    <bpmn:exclusiveGateway id="Again" default="f5"><bpmn:incoming>f4</bpmn:incoming><bpmn:outgoing>f5</bpmn:outgoing><bpmn:outgoing>f6</bpmn:outgoing></bpmn:exclusiveGateway>
    <bpmn:endEvent id="HostEnd"><bpmn:incoming>f5</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="f1" sourceRef="HostStart" targetRef="Init" />
    <bpmn:sequenceFlow id="f2" sourceRef="Init" targetRef="Join" />
    <bpmn:sequenceFlow id="f3" sourceRef="Join" targetRef="Call" />
    <bpmn:sequenceFlow id="f4" sourceRef="Call" targetRef="Again" />
    <bpmn:sequenceFlow id="f5" sourceRef="Again" targetRef="HostEnd" />
    <bpmn:sequenceFlow id="f6" sourceRef="Again" targetRef="Join"><bpmn:conditionExpression>i &lt; 3</bpmn:conditionExpression></bpmn:sequenceFlow>
  </bpmn:process>
</bpmn:definitions>
""")

looping_child = ("looping_child.bpmn", f"""
<bpmn:definitions {_BPMN} xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="looping_child" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="LoopingChild" isExecutable="true">
    <bpmn:startEvent id="ChildStart"><bpmn:outgoing>c1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:scriptTask id="Count"><bpmn:incoming>c1</bpmn:incoming><bpmn:outgoing>c2</bpmn:outgoing><bpmn:script>i = i + 1</bpmn:script></bpmn:scriptTask>
    <bpmn:callActivity id="Each" calledElement="LoopingGrandchild">
      <bpmn:incoming>c2</bpmn:incoming><bpmn:outgoing>c3</bpmn:outgoing>
      <bpmn:multiInstanceLoopCharacteristics isSequential="true">
        <bpmn:loopCardinality xsi:type="bpmn:tFormalExpression">2</bpmn:loopCardinality>
      </bpmn:multiInstanceLoopCharacteristics>
    </bpmn:callActivity>
    <bpmn:endEvent id="ChildEnd"><bpmn:incoming>c3</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="c1" sourceRef="ChildStart" targetRef="Count" />
    <bpmn:sequenceFlow id="c2" sourceRef="Count" targetRef="Each" />
    <bpmn:sequenceFlow id="c3" sourceRef="Each" targetRef="ChildEnd" />
  </bpmn:process>
</bpmn:definitions>
""")

looping_grandchild = ("looping_grandchild.bpmn", f"""
<bpmn:definitions {_BPMN} id="looping_grandchild" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="LoopingGrandchild" isExecutable="true">
    <bpmn:startEvent id="GrandchildStart"><bpmn:outgoing>g1</bpmn:outgoing></bpmn:startEvent>
    <bpmn:endEvent id="GrandchildEnd"><bpmn:incoming>g1</bpmn:incoming></bpmn:endEvent>
    <bpmn:sequenceFlow id="g1" sourceRef="GrandchildStart" targetRef="GrandchildEnd" />
  </bpmn:process>
</bpmn:definitions>
""")


def _lazy_loads_by_walking_the_tree(workflow):
    specs = set()
    for t in workflow.get_tasks(task_filter=TaskFilter(spec_class=CallActivity)):
        specs.add(t.task_spec.spec)
    for t in workflow.get_tasks(task_filter=TaskFilter(spec_class=LoopTask)):
        task_spec = t.workflow.spec.task_specs.get(t.task_spec.task_spec)
        if task_spec and hasattr(task_spec, "spec"):
            specs.add(task_spec.spec)
    return specs


def test_lazy_loads_matches_a_walk_of_the_task_tree_at_every_step():
    specs, err = specs_from_xml([looping_host, looping_child, looping_grandchild])
    assert err is None
    workflow = runner.hydrate_workflow(specs, {})

    seen = []
    steps = 0
    while not workflow.completed:
        workflow.get_tasks(state=TaskState.READY)[0].run()
        steps += 1
        found = set(runner.lazy_loads(workflow))
        assert found == _lazy_loads_by_walking_the_tree(workflow)
        seen.append(found)

    assert workflow.data["i"] == 3
    assert steps > 30
    assert seen[0] == {"LoopingChild"}
    assert seen[-1] == {"LoopingChild", "LoopingGrandchild"}

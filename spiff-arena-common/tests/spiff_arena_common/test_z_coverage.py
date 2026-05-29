import json

from spiff_arena_common.coverage import task_coverage
from spiff_arena_common.runner import specs_from_xml
from spiff_arena_common.tester import run_tests


subprocess = ("subprocess.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_Subprocess" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Subprocess" name="Subprocess" isExecutable="true">
    <bpmn:startEvent id="StartEvent_Subprocess">
      <bpmn:outgoing>Flow_Subprocess_Start</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:scriptTask id="Task_Subprocess" name="Subprocess Step">
      <bpmn:incoming>Flow_Subprocess_Start</bpmn:incoming>
      <bpmn:outgoing>Flow_Subprocess_End</bpmn:outgoing>
      <bpmn:script>subprocess_ran = True</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_Subprocess">
      <bpmn:incoming>Flow_Subprocess_End</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_Subprocess_Start" sourceRef="StartEvent_Subprocess" targetRef="Task_Subprocess" />
    <bpmn:sequenceFlow id="Flow_Subprocess_End" sourceRef="Task_Subprocess" targetRef="EndEvent_Subprocess" />
  </bpmn:process>
</bpmn:definitions>
""")

parent = ("parent.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_Parent" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Parent" name="Parent" isExecutable="true">
    <bpmn:startEvent id="StartEvent_Parent">
      <bpmn:outgoing>Flow_Parent_First</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:callActivity id="Call_First" name="Run Subprocess Once" calledElement="Subprocess">
      <bpmn:incoming>Flow_Parent_First</bpmn:incoming>
      <bpmn:outgoing>Flow_Parent_Second</bpmn:outgoing>
    </bpmn:callActivity>
    <bpmn:callActivity id="Call_Second" name="Run Subprocess Twice" calledElement="Subprocess">
      <bpmn:incoming>Flow_Parent_Second</bpmn:incoming>
      <bpmn:outgoing>Flow_Parent_End</bpmn:outgoing>
    </bpmn:callActivity>
    <bpmn:endEvent id="EndEvent_Parent">
      <bpmn:incoming>Flow_Parent_End</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_Parent_First" sourceRef="StartEvent_Parent" targetRef="Call_First" />
    <bpmn:sequenceFlow id="Flow_Parent_Second" sourceRef="Call_First" targetRef="Call_Second" />
    <bpmn:sequenceFlow id="Flow_Parent_End" sourceRef="Call_Second" targetRef="EndEvent_Parent" />
  </bpmn:process>
</bpmn:definitions>
""")

parent_test = ("parent_test.bpmn", """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" id="Definitions_Parent_Test" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Parent_Test" name="Parent_Test" isExecutable="true">
    <bpmn:startEvent id="StartEvent_Parent_Test">
      <bpmn:outgoing>Flow_Test_Run</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:callActivity id="Call_Parent" name="Run Parent" calledElement="Parent">
      <bpmn:incoming>Flow_Test_Run</bpmn:incoming>
      <bpmn:outgoing>Flow_Test_Result</bpmn:outgoing>
    </bpmn:callActivity>
    <bpmn:scriptTask id="Task_Test_Result" name="Test Result">
      <bpmn:incoming>Flow_Test_Result</bpmn:incoming>
      <bpmn:outgoing>Flow_Test_End</bpmn:outgoing>
      <bpmn:script>
def test():
  import unittest

  from spiff_arena_common.tester import run_test_cases

  class ParentRunsTwice(unittest.TestCase):
    def runTest(self):
      self.assertTrue(subprocess_ran)

  return run_test_cases([ParentRunsTwice()])

spiff_testFixture = {"pendingTaskStack": []}
spiff_testResult = test()
      </bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_Parent_Test">
      <bpmn:incoming>Flow_Test_End</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_Test_Run" sourceRef="StartEvent_Parent_Test" targetRef="Call_Parent" />
    <bpmn:sequenceFlow id="Flow_Test_Result" sourceRef="Call_Parent" targetRef="Task_Test_Result" />
    <bpmn:sequenceFlow id="Flow_Test_End" sourceRef="Task_Test_Result" targetRef="EndEvent_Parent_Test" />
  </bpmn:process>
</bpmn:definitions>
""")


def test_task_coverage_ignores_subprocess_tasks_completed_in_parent_state():
    parsed = []
    for file in [subprocess, parent, parent_test]:
        specs, err = specs_from_xml([file])
        assert err is None
        parsed.append((file[0], specs))

    ctx, result, _ = run_tests(parsed)

    assert result.wasSuccessful()

    _, tally = task_coverage(ctx)

    parent_tally = tally.breakdown["Parent"]
    assert parent_tally.completed == parent_tally.all
    assert parent_tally.percent == 100


def test_task_coverage_counts_only_task_specs_with_bpmn_ids():
    class FakeTestCase:
        state = {
            "subprocesses": {
                "fake": {
                    "spec": "FakeProcess",
                    "tasks": {
                        "generated": {"state": 64, "task_spec": "Start"},
                        "real": {"state": 64, "task_spec": "Task_One"},
                    },
                },
            },
        }

    class FakeContext:
        test_cases = [FakeTestCase()]
        specs = {
            "FakeProcess": """
                {
                    "spec": {
                        "task_specs": {
                            "Start": {"bpmn_id": null},
                            "Task_One": {"bpmn_id": "Task_One"},
                            "Task_Two": {"bpmn_id": "Task_Two"}
                        }
                    }
                }
            """,
        }

    cov, tally = task_coverage(FakeContext())

    assert cov.all["FakeProcess"] == {"Task_One", "Task_Two"}
    assert cov.completed["FakeProcess"] == {"Task_One"}
    assert cov.missing["FakeProcess"] == {"Task_Two"}
    assert tally.breakdown["FakeProcess"].completed == 1
    assert tally.breakdown["FakeProcess"].all == 2


def test_task_coverage_counts_embedded_subprocess_tasks_but_not_call_activity_tasks():
    def specs(spec, subprocess_specs=None):
        return {
            "spec": spec,
            "subprocess_specs": subprocess_specs or {},
        }

    parent_spec = {
        "name": "Parent",
        "task_specs": {
            "Start": {"bpmn_id": "Start", "typename": "StartEvent"},
            "Embedded": {
                "bpmn_id": "Embedded",
                "typename": "SubWorkflowTask",
                "spec": "EmbeddedProcess",
            },
            "Call_Other": {
                "bpmn_id": "Call_Other",
                "typename": "CallActivity",
                "spec": "CalledProcess",
            },
            "End": {"bpmn_id": "End", "typename": "EndEvent"},
        },
    }
    embedded_spec = {
        "name": "EmbeddedProcess",
        "task_specs": {
            "Embedded_Start": {"bpmn_id": "Embedded_Start", "typename": "StartEvent"},
            "Embedded_Task": {"bpmn_id": "Embedded_Task", "typename": "ScriptTask"},
            "Embedded_End": {"bpmn_id": "Embedded_End", "typename": "EndEvent"},
        },
    }
    called_spec = {
        "name": "CalledProcess",
        "task_specs": {
            "Called_Task": {"bpmn_id": "Called_Task", "typename": "ScriptTask"},
        },
    }
    serialized_specs = {
        "Parent": json.dumps(specs(parent_spec, {"EmbeddedProcess": embedded_spec})),
        "CalledProcess": json.dumps(specs(called_spec)),
    }

    class FakeTestCase:
        coverage_spec_id = "Parent"
        state = {
            "tasks": {
                "start": {"state": 64, "task_spec": "Start"},
                "embedded": {"state": 64, "task_spec": "Embedded"},
                "call": {"state": 64, "task_spec": "Call_Other"},
                "end": {"state": 64, "task_spec": "End"},
            },
            "subprocesses": {
                "embedded": {
                    "spec": "EmbeddedProcess",
                    "tasks": {
                        "embedded_start": {"state": 64, "task_spec": "Embedded_Start"},
                        "embedded_task": {"state": 64, "task_spec": "Embedded_Task"},
                        "embedded_end": {"state": 64, "task_spec": "Embedded_End"},
                    },
                },
                "called": {
                    "spec": "CalledProcess",
                    "tasks": {
                        "called_task": {"state": 64, "task_spec": "Called_Task"},
                    },
                },
            },
        }

    class FakeContext:
        test_cases = [FakeTestCase()]
        specs = serialized_specs

    cov, tally = task_coverage(FakeContext())

    assert cov.all["Parent"] == {
        "Start",
        "Embedded",
        "Call_Other",
        "End",
        "Embedded_Start",
        "Embedded_Task",
        "Embedded_End",
    }
    assert cov.completed["Parent"] == cov.all["Parent"]
    assert cov.all["CalledProcess"] == {"Called_Task"}
    assert cov.completed["CalledProcess"] == {"Called_Task"}
    assert tally.breakdown["Parent"].completed == 7
    assert tally.breakdown["Parent"].all == 7
    assert tally.breakdown["CalledProcess"].completed == 1
    assert tally.breakdown["CalledProcess"].all == 1

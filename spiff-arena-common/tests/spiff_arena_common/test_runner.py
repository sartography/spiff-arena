import json
from types import SimpleNamespace

from SpiffWorkflow.task import TaskState

from spiff_arena_common import runner


class FakeTask:
    def __init__(self, *, bpmn_id=None, task_spec=None):
        self.state = TaskState.READY
        self.task_spec = task_spec or SimpleNamespace(bpmn_id=bpmn_id)
        self.data = {}
        self.run_calls = 0

    def run(self):
        self.run_calls += 1


def test_advance_workflow_falls_back_to_root_ready_lookup_without_refresh(monkeypatch):
    task = FakeTask()
    root_ready_task = FakeTask()
    workflow = SimpleNamespace(
        subprocess_specs={},
        refresh_waiting_tasks=lambda: (_ for _ in ()).throw(
            AssertionError("refresh_waiting_tasks should not be called")
        ),
    )

    monkeypatch.setattr(runner, "lazy_loads", lambda workflow: [])
    next_task_calls = []

    def fake_next_task(workflow, state, from_task=None):
        next_task_calls.append(from_task)
        if from_task is task:
            return None
        if from_task is None and root_ready_task.run_calls == 0:
            return root_ready_task
        return None

    monkeypatch.setattr(runner, "next_task", fake_next_task)
    monkeypatch.setattr(
        runner,
        "build_response",
        lambda workflow, error, compress_response=False, lazy_loads_result=None, session_id=None: {
            "status": "ok",
            "error": error,
            "lazy_loads": lazy_loads_result,
        },
    )

    result = runner._advance_workflow(workflow, task, "greedy")

    assert task.run_calls == 1
    assert root_ready_task.run_calls == 1
    assert next_task_calls == [task, None, root_ready_task, None]
    assert result == {"status": "ok", "error": None, "lazy_loads": []}


def test_custom_environment_get_current_task_data_filters_internal_keys():
    context = {
        "visible": 1,
        "__builtins__": {"len": len},
        "__annotations__": {"visible": int},
    }

    result = runner.CustomEnvironment().execute(
        "result = get_current_task_data()",
        context,
    )

    assert result is True
    assert context["result"] == {"visible": 1}


def test_advance_workflow_prints_unittest_break_when_no_ready_task_is_unexpected(monkeypatch, capsys):
    task = FakeTask(bpmn_id="InitialTask")
    workflow = SimpleNamespace(subprocess_specs={}, completed=False)

    monkeypatch.setattr(runner, "lazy_loads", lambda workflow: [])
    monkeypatch.setattr(runner, "next_task", lambda workflow, state, from_task=None: None)
    monkeypatch.setattr(
        runner,
        "build_response",
        lambda workflow, error, compress_response=False, lazy_loads_result=None, session_id=None: {
            "status": "ok",
            "error": error,
            "lazy_loads": lazy_loads_result,
        },
    )

    result = runner._advance_workflow(workflow, task, "unittest")

    captured = capsys.readouterr()
    event = json.loads(captured.out.strip())

    assert result == {"status": "ok", "error": None, "lazy_loads": []}
    assert event["event"] == "unittest-break"
    assert event["reason"] == "no_ready_task"
    assert event["strategy"] == "unittest"
    assert event["task_id"] == "InitialTask"


def test_advance_workflow_does_not_print_unittest_break_when_workflow_completed(monkeypatch, capsys):
    task = FakeTask(bpmn_id="InitialTask")
    workflow = SimpleNamespace(subprocess_specs={}, completed=True)

    monkeypatch.setattr(runner, "lazy_loads", lambda workflow: [])
    monkeypatch.setattr(runner, "next_task", lambda workflow, state, from_task=None: None)
    monkeypatch.setattr(
        runner,
        "build_response",
        lambda workflow, error, compress_response=False, lazy_loads_result=None, session_id=None: {
            "status": "ok",
            "error": error,
            "lazy_loads": lazy_loads_result,
        },
    )

    result = runner._advance_workflow(workflow, task, "unittest")

    captured = capsys.readouterr()

    assert result == {"status": "ok", "error": None, "lazy_loads": []}
    assert captured.out == ""


def test_advance_workflow_prints_unittest_break_when_fixture_task_mismatches(monkeypatch, capsys):
    class CustomUserTaskSpec:
        def __init__(self, bpmn_id):
            self.bpmn_id = bpmn_id

    initial_task = FakeTask(bpmn_id="InitialTask")
    fixture_task = FakeTask(task_spec=CustomUserTaskSpec("ActualTask"))
    fixture_task.data["spiff_testFixture"] = {
        "pendingTaskStack": [{"id": "ExpectedTask", "data": {"ok": True}}],
    }
    workflow = SimpleNamespace(subprocess_specs={}, data={}, completed=False)

    next_calls = []

    def fake_next_task(workflow, state, from_task=None):
        next_calls.append(from_task)
        if from_task is initial_task:
            return fixture_task
        return None

    monkeypatch.setattr(runner, "lazy_loads", lambda workflow: [])
    monkeypatch.setattr(runner, "next_task", fake_next_task)
    monkeypatch.setattr(
        runner,
        "build_response",
        lambda workflow, error, compress_response=False, lazy_loads_result=None, session_id=None: {
            "status": "ok",
            "error": error,
            "lazy_loads": lazy_loads_result,
        },
    )

    result = runner._advance_workflow(workflow, initial_task, "unittest")

    captured = capsys.readouterr()
    event = json.loads(captured.out.strip())

    assert result == {"status": "ok", "error": None, "lazy_loads": []}
    assert next_calls == [initial_task]
    assert event["event"] == "unittest-break"
    assert event["reason"] == "fixture_task_mismatch"
    assert event["task_id"] == "ActualTask"
    assert event["expected_task_id"] == "ExpectedTask"


def test_service_task_connector_error_follows_matching_error_boundary_event(monkeypatch):
    bpmn = """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="Definitions_error_boundary" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_error_boundary" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_start_service</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_start_service" sourceRef="StartEvent_1" targetRef="ServiceTask_1" />
    <bpmn:serviceTask id="ServiceTask_1" name="Service Task">
      <bpmn:extensionElements>
        <spiffworkflow:serviceTaskOperator id="http/GetRequestV2" resultVariable="response">
          <spiffworkflow:parameters>
            <spiffworkflow:parameter id="url" type="str" value="&quot;https://example.invalid&quot;" />
          </spiffworkflow:parameters>
        </spiffworkflow:serviceTaskOperator>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_start_service</bpmn:incoming>
      <bpmn:outgoing>Flow_service_normal</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_service_normal" sourceRef="ServiceTask_1" targetRef="Script_normal" />
    <bpmn:scriptTask id="Script_normal">
      <bpmn:incoming>Flow_service_normal</bpmn:incoming>
      <bpmn:outgoing>Flow_normal_end</bpmn:outgoing>
      <bpmn:script>route = "normal"</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_normal">
      <bpmn:incoming>Flow_normal_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_normal_end" sourceRef="Script_normal" targetRef="EndEvent_normal" />
    <bpmn:boundaryEvent id="Boundary_missing_schema" attachedToRef="ServiceTask_1">
      <bpmn:outgoing>Flow_boundary_handled</bpmn:outgoing>
      <bpmn:errorEventDefinition id="ErrorDefinition_missing_schema" errorRef="MissingSchema" />
    </bpmn:boundaryEvent>
    <bpmn:sequenceFlow id="Flow_boundary_handled" sourceRef="Boundary_missing_schema" targetRef="Script_handled" />
    <bpmn:scriptTask id="Script_handled">
      <bpmn:incoming>Flow_boundary_handled</bpmn:incoming>
      <bpmn:outgoing>Flow_handled_end</bpmn:outgoing>
      <bpmn:script>route = "handled"</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_handled">
      <bpmn:incoming>Flow_handled_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_handled_end" sourceRef="Script_handled" targetRef="EndEvent_handled" />
  </bpmn:process>
  <bpmn:error id="MissingSchema" name="MissingSchema" errorCode="MissingSchema" />
</bpmn:definitions>
"""

    def connector_error(*_args, **_kwargs):
        return json.dumps(
            {
                "command_response": {"body": "{}", "mimetype": "application/json"},
                "command_response_version": 2,
                "error": {
                    "error_code": "MissingSchema",
                    "message": "No schema supplied",
                },
            }
        )

    monkeypatch.setattr(runner.CustomScriptEngine, "call_service", connector_error)

    specs, err = runner.specs_from_xml([("error_boundary.bpmn", bpmn)])
    assert err is None

    result = None
    for _ in range(10):
        result = json.loads(
            runner.advance_workflow(
                specs,
                None,
                None,
                "greedy",
                None,
                session_id="error-boundary-test",
            )
        )
        if result["completed"] or result["status"] != "ok":
            break

    assert result["status"] == "ok"
    assert result["completed"] is True
    assert result["result"]["route"] == "handled"


def test_started_service_task_http_status_completion_follows_matching_error_boundary_event():
    bpmn = """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="Definitions_started_http_error_boundary" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_started_http_error_boundary" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_start_service</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_start_service" sourceRef="StartEvent_1" targetRef="ServiceTask_1" />
    <bpmn:serviceTask id="ServiceTask_1" name="Service Task">
      <bpmn:extensionElements>
        <spiffworkflow:serviceTaskOperator id="http/GetRequest" resultVariable="response">
          <spiffworkflow:parameters>
            <spiffworkflow:parameter id="url" type="str" value="&quot;https://example.invalid/missing&quot;" />
          </spiffworkflow:parameters>
        </spiffworkflow:serviceTaskOperator>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_start_service</bpmn:incoming>
      <bpmn:outgoing>Flow_service_normal</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_service_normal" sourceRef="ServiceTask_1" targetRef="Script_normal" />
    <bpmn:scriptTask id="Script_normal">
      <bpmn:incoming>Flow_service_normal</bpmn:incoming>
      <bpmn:outgoing>Flow_normal_end</bpmn:outgoing>
      <bpmn:script>route = "normal"</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_normal">
      <bpmn:incoming>Flow_normal_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_normal_end" sourceRef="Script_normal" targetRef="EndEvent_normal" />
    <bpmn:boundaryEvent id="Boundary_http_404" attachedToRef="ServiceTask_1">
      <bpmn:outgoing>Flow_boundary_handled</bpmn:outgoing>
      <bpmn:errorEventDefinition id="ErrorDefinition_http_404" errorRef="HttpError404" />
    </bpmn:boundaryEvent>
    <bpmn:sequenceFlow id="Flow_boundary_handled" sourceRef="Boundary_http_404" targetRef="Script_handled" />
    <bpmn:scriptTask id="Script_handled">
      <bpmn:incoming>Flow_boundary_handled</bpmn:incoming>
      <bpmn:outgoing>Flow_handled_end</bpmn:outgoing>
      <bpmn:script>route = "handled"</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_handled">
      <bpmn:incoming>Flow_handled_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_handled_end" sourceRef="Script_handled" targetRef="EndEvent_handled" />
  </bpmn:process>
  <bpmn:error id="HttpError404" name="HttpError404" errorCode="HttpError404" />
</bpmn:definitions>
"""

    specs, err = runner.specs_from_xml([("started_http_error_boundary.bpmn", bpmn)])
    assert err is None

    session_id = "started-http-error-boundary-test"
    first_step = json.loads(
        runner.advance_workflow(specs, None, None, "oneAtATime", None, session_id=session_id)
    )
    start_task = next(
        task
        for task in first_step["pending_tasks"]
        if task["task_spec"]["typename"] == "StartEvent"
    )
    service_ready_step = json.loads(
        runner.advance_workflow(
            specs,
            None,
            {"id": start_task["id"], "data": {}},
            "oneAtATime",
            None,
            session_id=session_id,
        )
    )
    service_task = next(
        task
        for task in service_ready_step["pending_tasks"]
        if task["task_spec"]["typename"] == "ServiceTask"
    )

    started_step = json.loads(
        runner.advance_workflow(
            specs,
            None,
            {"id": service_task["id"], "data": {}},
            "oneAtATime",
            None,
            session_id=session_id,
        )
    )
    started_service_task = next(
        task
        for task in started_step["pending_tasks"]
        if task["id"] == service_task["id"]
    )
    assert started_service_task["state"] == TaskState.STARTED

    result = json.loads(
        runner.advance_workflow(
            specs,
            None,
            {
                "id": service_task["id"],
                "data": {
                    "response": {
                        "body": {},
                        "mimetype": "application/json",
                        "http_status": 404,
                        "headers": {},
                        "command_response": {
                            "body": {},
                            "mimetype": "application/json",
                            "http_status": 404,
                            "headers": {},
                        },
                        "command_response_version": 2,
                        "error": {
                            "error_code": "HttpError404",
                            "message": "HTTP 404 error from service. Response: {}",
                        },
                        "operator_identifier": "http/GetRequest",
                    }
                },
            },
            "greedy",
            None,
            session_id=session_id,
        )
    )

    assert result["status"] == "ok"
    assert result["completed"] is True
    assert result["result"]["route"] == "handled"


def test_service_task_http_status_response_follows_matching_error_boundary_event(monkeypatch):
    bpmn = """
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core" id="Definitions_http_error_boundary" targetNamespace="http://bpmn.io/schema/bpmn">
  <bpmn:process id="Process_http_error_boundary" isExecutable="true">
    <bpmn:startEvent id="StartEvent_1">
      <bpmn:outgoing>Flow_start_service</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_start_service" sourceRef="StartEvent_1" targetRef="ServiceTask_1" />
    <bpmn:serviceTask id="ServiceTask_1" name="Service Task">
      <bpmn:extensionElements>
        <spiffworkflow:serviceTaskOperator id="http/GetRequestV2" resultVariable="response">
          <spiffworkflow:parameters>
            <spiffworkflow:parameter id="url" type="str" value="&quot;https://example.invalid/missing&quot;" />
          </spiffworkflow:parameters>
        </spiffworkflow:serviceTaskOperator>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_start_service</bpmn:incoming>
      <bpmn:outgoing>Flow_service_normal</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_service_normal" sourceRef="ServiceTask_1" targetRef="Script_normal" />
    <bpmn:scriptTask id="Script_normal">
      <bpmn:incoming>Flow_service_normal</bpmn:incoming>
      <bpmn:outgoing>Flow_normal_end</bpmn:outgoing>
      <bpmn:script>route = "normal"</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_normal">
      <bpmn:incoming>Flow_normal_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_normal_end" sourceRef="Script_normal" targetRef="EndEvent_normal" />
    <bpmn:boundaryEvent id="Boundary_http_404" attachedToRef="ServiceTask_1">
      <bpmn:outgoing>Flow_boundary_handled</bpmn:outgoing>
      <bpmn:errorEventDefinition id="ErrorDefinition_http_404" errorRef="ServiceTaskHttpError404" />
    </bpmn:boundaryEvent>
    <bpmn:sequenceFlow id="Flow_boundary_handled" sourceRef="Boundary_http_404" targetRef="Script_handled" />
    <bpmn:scriptTask id="Script_handled">
      <bpmn:incoming>Flow_boundary_handled</bpmn:incoming>
      <bpmn:outgoing>Flow_handled_end</bpmn:outgoing>
      <bpmn:script>route = "handled"</bpmn:script>
    </bpmn:scriptTask>
    <bpmn:endEvent id="EndEvent_handled">
      <bpmn:incoming>Flow_handled_end</bpmn:incoming>
    </bpmn:endEvent>
    <bpmn:sequenceFlow id="Flow_handled_end" sourceRef="Script_handled" targetRef="EndEvent_handled" />
  </bpmn:process>
  <bpmn:error id="ServiceTaskHttpError404" name="ServiceTaskHttpError404" errorCode="ServiceTaskHttpError404" />
</bpmn:definitions>
"""

    def connector_404(*_args, **_kwargs):
        return json.dumps(
            {
                "command_response": {
                    "body": "not found",
                    "mimetype": "text/plain",
                    "http_status": 404,
                },
                "command_response_version": 2,
                "error": None,
            }
        )

    monkeypatch.setattr(runner.CustomScriptEngine, "call_service", connector_404)

    specs, err = runner.specs_from_xml([("http_error_boundary.bpmn", bpmn)])
    assert err is None

    result = None
    for _ in range(10):
        result = json.loads(
            runner.advance_workflow(
                specs,
                None,
                None,
                "greedy",
                None,
                session_id="http-error-boundary-test",
            )
        )
        if result["completed"] or result["status"] != "ok":
            break

    assert result["status"] == "ok"
    assert result["completed"] is True
    assert result["result"]["route"] == "handled"

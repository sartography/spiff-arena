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

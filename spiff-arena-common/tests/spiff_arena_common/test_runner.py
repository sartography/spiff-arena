from types import SimpleNamespace

from SpiffWorkflow.task import TaskState

from spiff_arena_common import runner


class FakeTask:
    def __init__(self):
        self.state = TaskState.READY
        self.task_spec = SimpleNamespace(bpmn_id=None)
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

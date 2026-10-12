import json

from spiff_arena_common import runner
from spiff_arena_common.runner import advance_workflow, specs_from_xml

from test_lazy_load import looping_child, looping_grandchild, looping_host


def _walk(session_id, **options):
    """Run the looping workflow one task at a time and return every response."""
    specs, err = specs_from_xml([looping_host, looping_child, looping_grandchild])
    assert err is None
    runner.clear_workflow_cache(session_id)
    state = {}
    steps = []
    while not steps or not steps[-1]["completed"]:
        steps.append(json.loads(advance_workflow(
            specs, state, None, "oneAtATime", None, session_id=session_id, **options,
        )))
        assert steps[-1]["status"] == "ok"
        state = None
    return steps


def _without_ids(step):
    """A response without its random task ids, and without the diagram state."""
    return {
        **{key: value for key, value in step.items() if key != "state"},
        "pending_tasks": [
            {key: value for key, value in task.items() if key != "id"}
            for task in step.get("pending_tasks", [])
        ],
        "lazy_loads": sorted(step.get("lazy_loads", [])),
    }


def test_step_history_and_state_are_kept_by_default():
    steps = _walk("history-default")
    history = runner._step_history_cache["history-default"]

    assert len(steps) > 30
    assert all("state" in step for step in steps)
    assert [step["step_idx"] for step in steps] == list(range(len(steps)))
    assert len(history) == len(steps)
    assert all(isinstance(state, dict) for state in history)


def test_step_history_and_state_can_be_left_out_without_changing_the_run():
    kept = _walk("history-kept")
    skipped = _walk("history-skipped", record_step_history=False, include_state=False)

    assert not any("state" in step for step in skipped)
    assert [_without_ids(step) for step in skipped] == [_without_ids(step) for step in kept]
    # Each step keeps its index but holds no state to jump back to.
    assert runner._step_history_cache["history-skipped"] == [None] * len(skipped)


def test_the_two_options_are_independent():
    no_history = _walk("history-only-skipped", record_step_history=False)
    no_state = _walk("state-only-skipped", include_state=False)

    assert all("state" in step for step in no_history)
    assert runner._step_history_cache["history-only-skipped"] == [None] * len(no_history)
    assert not any("state" in step for step in no_state)
    assert all(isinstance(state, dict) for state in runner._step_history_cache["state-only-skipped"])

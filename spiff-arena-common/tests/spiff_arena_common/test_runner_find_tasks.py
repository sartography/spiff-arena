from SpiffWorkflow.bpmn.util.task import BpmnTaskFilter
from SpiffWorkflow.util.task import TaskFilter, TaskState

from spiff_arena_common import runner
from spiff_arena_common.runner import specs_from_xml

from test_lazy_load import looping_child, looping_grandchild, looping_host

PENDING = TaskState.STARTED | TaskState.READY | TaskState.WAITING


def _filters(workflow):
    spec_names = sorted({task.task_spec.name for task in workflow.get_tasks()})
    return [
        TaskFilter(state=TaskState.READY),
        TaskFilter(state=PENDING),
        TaskFilter(state=TaskState.COMPLETED),
        TaskFilter(state=TaskState.ANY_MASK),
        TaskFilter(state=TaskState.PREDICTED_MASK),
        TaskFilter(state=TaskState.FUTURE | TaskState.READY),
        BpmnTaskFilter(state=TaskState.ANY_MASK, lane=None),
        *(TaskFilter(state=TaskState.ANY_MASK, spec_name=name) for name in spec_names[:3]),
    ]


def _assert_same_as_get_tasks(workflow):
    checked = 0
    all_tasks = workflow.get_tasks()
    # From the root, and from a spread of tasks including ones that own subprocesses.
    first_tasks = [None, *all_tasks[:: max(1, len(all_tasks) // 12)]]
    first_tasks += [task for task in all_tasks if task.id in workflow.subprocesses][:3]
    for task_filter in _filters(workflow):
        for first_task in first_tasks:
            expected = workflow.get_tasks(first_task=first_task, task_filter=task_filter)
            found = runner.find_tasks(workflow, task_filter, first_task)
            assert [task.id for task in found] == [task.id for task in expected]
            checked += 1
    for state in (TaskState.READY, PENDING):
        expected = workflow.get_tasks(state=state)
        found = runner.next_task(workflow, state)
        assert (found.id if found else None) == (expected[0].id if expected else None)
    return checked


def test_find_tasks_matches_get_tasks_at_every_step_and_after_a_reset():
    specs, err = specs_from_xml([looping_host, looping_child, looping_grandchild])
    assert err is None
    workflow = runner.hydrate_workflow(specs, {})

    checked = 0
    steps = 0
    completed_in_subprocess = []
    while not workflow.completed:
        task = workflow.get_tasks(state=TaskState.READY)[0]
        task.run()
        steps += 1
        if task.workflow is not workflow:
            completed_in_subprocess.append(task)
        checked += _assert_same_as_get_tasks(workflow)

        # Half way through, rewind into a subprocess and carry on from there.
        if steps == 20 and completed_in_subprocess:
            workflow.reset_from_task_id(completed_in_subprocess[len(completed_in_subprocess) // 2].id)
            checked += _assert_same_as_get_tasks(workflow)

    assert steps > 30
    assert len(workflow.subprocesses) > 3
    assert checked > 1000

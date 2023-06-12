# -*- coding: utf-8 -*-

import time
from SpiffWorkflow.workflow import Workflow
from SpiffWorkflow.specs.SubWorkflow import SubWorkflow


def on_reached_cb(workflow, task, taken_path):
    reached_key = "%s_reached" % str(task.get_name())
    n_reached = task.get_data(reached_key, 0) + 1
    task.set_data(**{reached_key:       n_reached,
                     'two':             2,
                     'three':           3,
                     'test_attribute1': 'false',
                     'test_attribute2': 'true'})

    # Collect a list of all data.
    atts = []
    for key, value in list(task.data.items()):
        if key in ['data',
                   'two',
                   'three',
                   'test_attribute1',
                   'test_attribute2']:
            continue
        if key.endswith('reached'):
            continue
        atts.append('='.join((key, str(value))))

    # Collect a list of all task data.
    props = []
    for key, value in list(task.task_spec.data.items()):
        props.append('='.join((key, str(value))))

    # Store the list of data in the workflow.
    atts = ';'.join(atts)
    props = ';'.join(props)
    old = task.get_data('data', '')
    data = task.get_name() + ': ' + atts + '/' + props + '\n'
    task.set_data(data=old + data)
    return True

def on_complete_cb(workflow, task, taken_path):
    # Record the path.
    indent = '  ' * (task._get_depth() - 1)
    taken_path.append('%s%s' % (indent, task.get_name()))
    # In workflows that load a subworkflow, the newly loaded children
    # will not have on_reached_cb() assigned. By using this function, we
    # re-assign the function in every step, thus making sure that new
    # children also call on_reached_cb().
    for child in task.children:
        track_task(child.task_spec, taken_path)
    return True

def on_entered_cb(workflow, task, taken_path):
    for child in task.children:
        track_task(child.task_spec, taken_path)
    return True

def track_task(task_spec, taken_path):
    # Disconnecting and reconnecting makes absolutely no sense but inexplicably these tests break
    # if just connected based on a check that they're not
    if task_spec.reached_event.is_connected(on_reached_cb):
        task_spec.reached_event.disconnect(on_reached_cb)
    task_spec.reached_event.connect(on_reached_cb, taken_path)
    if task_spec.completed_event.is_connected(on_complete_cb):
        task_spec.completed_event.disconnect(on_complete_cb)
    task_spec.completed_event.connect(on_complete_cb, taken_path)
    if isinstance(task_spec, SubWorkflow):
        if task_spec.entered_event.is_connected(on_entered_cb):
            task_spec.entered_event.disconnect(on_entered_cb)
        task_spec.entered_event.connect(on_entered_cb, taken_path)

def track_workflow(wf_spec, taken_path=None):
    if taken_path is None:
        taken_path = []
    for name in wf_spec.task_specs:
        track_task(wf_spec.task_specs[name], taken_path)
    return taken_path

def run_workflow(test, wf_spec, expected_path, expected_data, workflow=None):
    # Execute all tasks within the Workflow.
    if workflow is None:
        taken_path = track_workflow(wf_spec)
        workflow = Workflow(wf_spec)
    else:
        taken_path = track_workflow(workflow.spec)

    test.assertFalse(workflow.is_completed())
    try:
        # We allow the workflow to require a maximum of 5 seconds to
        # complete, to allow for testing long running tasks.
        for i in range(10):
            workflow.run_all(False)
            if workflow.is_completed():
                break
            time.sleep(0.5)
    except Exception:
        workflow.task_tree.dump()
        raise

    test.assertTrue(workflow.is_completed())

    # Check whether the correct route was taken.
    if expected_path is not None:
        taken_path = '\n'.join(taken_path) + '\n'
        test.assertEqual(taken_path, expected_path)

    # Check data availibility.
    if expected_data is not None:
        result = workflow.get_data('data', '')
        test.assertIn(result, expected_data)

    return workflow

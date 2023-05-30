# -*- coding: utf-8 -*-

from ..util import run_workflow
from .TaskSpecTest import TaskSpecTest
from SpiffWorkflow.specs.Transform import Transform
from SpiffWorkflow.specs.Simple import Simple


class TransformTest(TaskSpecTest):

    def create_instance(self):
        if 'testtask' in self.wf_spec.task_specs:
            del self.wf_spec.task_specs['testtask']

        return Transform(self.wf_spec,
                         'testtask',
                         description='foo',
                         transforms=[''])

    def testPattern(self):
        """
        Tests that we can create a task that executes a shell command
        and that the workflow can be called to complete such tasks.
        """
        task1 = Transform(self.wf_spec, 'First', transforms=[
            "my_task.set_data(foo=1)"])
        self.wf_spec.start.connect(task1)
        task2 = Transform(self.wf_spec, 'Second', transforms=[
            "my_task.set_data(foo=my_task.data['foo']+1)",
            "my_task.set_data(copy=my_task.data['foo'])"
        ])
        task1.connect(task2)
        task3 = Simple(self.wf_spec, 'Last')
        task2.connect(task3)

        expected = 'Start\n  First\n    Second\n      Last\n'
        workflow = run_workflow(self, self.wf_spec, expected, '')
        first = workflow.get_tasks_from_spec_name('First')[0]
        last = workflow.get_tasks_from_spec_name('Last')[0]
        self.assertEqual(first.data.get('foo'), 1)
        self.assertEqual(last.data.get('foo'), 2)
        self.assertEqual(last.data.get('copy'), 2)

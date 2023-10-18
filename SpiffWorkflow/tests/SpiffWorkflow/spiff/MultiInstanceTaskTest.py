from SpiffWorkflow.bpmn.workflow import BpmnWorkflow

from .BaseTestCase import BaseTestCase


class MultiInstanceTaskTest(BaseTestCase):

    def testMultiInstanceTask(self):
        spec, subprocesses = self.load_workflow_spec('spiff_multiinstance.bpmn', 'Process_1')
        self.workflow = BpmnWorkflow(spec, subprocesses)
        start = self.workflow.task_tree
        start.data = {'input_data': [1, 2, 3]}
        self.workflow.do_engine_steps()
        task = self.workflow.get_next_task(spec_name='any_task')
        self.workflow.do_engine_steps()

        self.save_restore()

        ready_tasks = self.get_ready_user_tasks()
        for task in ready_tasks:
            task.data['output_item'] = task.data['input_item'] * 2
            task.run()
            self.workflow.do_engine_steps()

        self.assertTrue(self.workflow.is_completed())
        self.assertDictEqual(self.workflow.data, {
            'input_data': [2, 3, 4],  # Prescript adds 1 to input
            'output_data': [3, 5, 7],  # Postscript subtracts 1 from output
        })

    def testMultiInstanceTaskWithInstanceScripts(self):
        spec, subprocesses = self.load_workflow_spec('script_on_mi.bpmn', 'Process_1')
        self.workflow = BpmnWorkflow(spec, subprocesses)
        start = self.workflow.get_next_task(spec_name='Start')
        start.data = {'input_data': [1, 2, 3]}
        self.workflow.do_engine_steps()
        task = self.workflow.get_next_task(spec_name='any_task')
        self.workflow.do_engine_steps()

        self.save_restore()

        ready_tasks = self.get_ready_user_tasks()
        for task in ready_tasks:
            task.data['output_item'] = task.data['input_item'] * 2
            task.run()
            self.workflow.do_engine_steps()

        self.assertTrue(self.workflow.is_completed())
        self.assertDictEqual(self.workflow.data, {
            'input_data': [1, 2, 3],  # Prescript modifies input item
            'output_data': [3, 5, 7],
        })
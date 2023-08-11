# -*- coding: utf-8 -*-

from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from .BpmnWorkflowTestCase import BpmnWorkflowTestCase

__author__ = 'matth'


class ResetSubProcessTest(BpmnWorkflowTestCase):
    """Assure we can reset a token to a previous task when we have
        a sub-workflow."""

    def setUp(self):
        spec, subprocesses = self.load_workflow_spec('resetworkflowA-*.bpmn', 'TopLevel')
        self.workflow = BpmnWorkflow(spec, subprocesses)

    def reload_save_restore(self):

        spec, subprocesses = self.load_workflow_spec('resetworkflowB-*.bpmn', 'TopLevel')
        self.workflow = BpmnWorkflow(spec, subprocesses)
        # Save and restore the workflow, without including the spec.
        # When loading the spec, use a slightly different spec.
        self.workflow.do_engine_steps()
        state = self.serializer.serialize_json(self.workflow)
        self.workflow = self.serializer.deserialize_json(state)
        self.workflow.spec = spec
        self.workflow.subprocess_specs = subprocesses

    def testSaveRestore(self):
        self.actualTest(True)

    def testResetToOuterWorkflowWhileInSubWorkflow(self):

        self.workflow.do_engine_steps()
        top_level_task = self.workflow.get_ready_user_tasks()[0]
        top_level_task.run()
        self.workflow.do_engine_steps()
        task = self.workflow.get_ready_user_tasks()[0]
        self.save_restore()
        top_level_task = self.workflow.get_tasks_from_spec_name('Task1')[0]
        self.workflow.reset_from_task_id(top_level_task.id)
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual(len(self.workflow.get_ready_user_tasks()), 1, "There should only be one task in a ready state.")
        self.assertEqual(task.get_name(), 'Task1')

    def actualTest(self, save_restore=False):

        self.workflow.do_engine_steps()
        self.assertEqual(1, len(self.workflow.get_ready_user_tasks()))
        task = self.workflow.get_ready_user_tasks()[0]
        task.run()
        self.workflow.do_engine_steps()
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual(task.get_name(),'SubTask2')
        task.run()
        self.workflow.do_engine_steps()
        task = self.workflow.get_tasks_from_spec_name('Task1')[0]
        task.reset_token(self.workflow.last_task.data)
        self.workflow.do_engine_steps()
        self.reload_save_restore()
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual(task.get_name(),'Task1')
        task.run()
        self.workflow.do_engine_steps()
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual(task.get_name(),'Subtask2')
        task.run()
        self.workflow.do_engine_steps()
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual(task.get_name(),'Subtask2A')
        task.run()
        self.workflow.do_engine_steps()
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual(task.get_name(),'Task2')
        task.run()
        self.workflow.do_engine_steps()
        self.assertTrue(self.workflow.is_completed())

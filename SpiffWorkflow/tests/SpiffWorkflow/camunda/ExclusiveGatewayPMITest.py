# -*- coding: utf-8 -*-

import unittest

from SpiffWorkflow.bpmn.workflow import BpmnWorkflow

from tests.SpiffWorkflow.camunda.BaseTestCase import BaseTestCase

__author__ = 'matth'


class ExclusiveGatewayPMITest(BaseTestCase):
    """The example bpmn diagram tests both a set cardinality from user input
    as well as looping over an existing array."""

    def setUp(self):
        spec, subprocesses = self.load_workflow_spec('default_gateway_pmi.bpmn', 'DefaultGateway')
        self.workflow = BpmnWorkflow(spec, subprocesses)

    def testRunThroughHappy(self):
        self.actual_test(False)

    def testRunThroughSaveRestore(self):
        self.actual_test(True)

    def testRunThroughHappyNo(self):
        self.actual_test(False,'No')

    def testRunThroughSaveRestoreNo(self):
        self.actual_test(True,'No')

    def actual_test(self, save_restore=False,response='Yes'):

        self.workflow.do_engine_steps()

        # Set initial array size to 3 in the first user form.
        task = self.workflow.get_ready_user_tasks()[0]
        self.assertEqual("DoStuff", task.task_spec.name)
        task.update_data({"morestuff": response})
        self.workflow.complete_task_from_id(task.id)
        self.workflow.do_engine_steps()
        if save_restore: self.save_restore()

        # Set the names of the 3 family members.
        if response == 'Yes':
            for i in range(3):
                task = self.workflow.get_ready_user_tasks()[0]
                if i == 0:
                    self.assertEqual("GetMoreStuff", task.task_spec.name)
                else:
                    self.assertEqual("GetMoreStuff_%d"%(i-1), task.task_spec.name)


                task.update_data({"stuff.addstuff": "Stuff %d"%i})
                self.workflow.complete_task_from_id(task.id)
                if save_restore: self.save_restore()
                self.workflow.do_engine_steps()

        if save_restore: self.save_restore()
        self.assertTrue(self.workflow.is_completed())



def suite():
    return unittest.TestLoader().loadTestsFromTestCase(ExclusiveGatewayPMITest)

if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

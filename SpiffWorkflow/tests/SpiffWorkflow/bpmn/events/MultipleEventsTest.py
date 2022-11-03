# -*- coding: utf-8 -*-
import unittest

from SpiffWorkflow.bpmn.specs.events.event_definitions import CancelEventDefinition, SignalEventDefinition
from SpiffWorkflow.task import TaskState
from SpiffWorkflow.bpmn.workflow import BpmnWorkflow
from tests.SpiffWorkflow.bpmn.BpmnWorkflowTestCase import BpmnWorkflowTestCase

__author__ = 'kellym'


class MultipleEventsTest(BpmnWorkflowTestCase):

    def setUp(self):
        self.spec, self.subprocesses = self.load_workflow_spec('multipleEvents.bpmn', 'SignalAndCancel')
        self.workflow = BpmnWorkflow(self.spec, self.subprocesses)
        self.workflow.do_engine_steps()
        ready_tasks = self.workflow.get_tasks(TaskState.READY)
        self.assertEqual("hello", ready_tasks[0].get_name())

    def test_cancel_does_nothing_if_no_one_is_listening(self,save_restore = False):

        # Send cancel notifications to the workflow
        self.workflow.catch(SignalEventDefinition('cancel'))  # generate a cancel signal.
        self.workflow.catch(CancelEventDefinition())

        # Nothing should have happened.
        ready_tasks = self.workflow.get_tasks(TaskState.READY)
        self.assertEqual("hello", ready_tasks[0].get_name())

    def test_cancel_works_with_signal(self,save_restore = False):

        task = self.workflow.get_tasks(TaskState.READY)[0]

        # Move to User Task 1
        self.workflow.complete_task_from_id(task.id)
        self.workflow.do_engine_steps()
        task = self.workflow.get_tasks(TaskState.READY)[0]
        self.assertEqual('UserTaskOne', task.get_name())

        # Send cancel notifications to the workflow
        self.workflow.catch(SignalEventDefinition('cancel'))  # generate a cancel signal.
        self.workflow.catch(CancelEventDefinition())
        self.workflow.do_engine_steps()

        # The cancel event should have been called.
        self.assertEqual("cancel_signal", self.workflow.last_task.data['cancel'])


    def test_cancel_works_with_cancel_Event(self,save_restore = False):

        task = self.workflow.get_tasks(TaskState.READY)[0]

        # Move to User Task 2
        self.workflow.complete_task_from_id(task.id)
        self.workflow.do_engine_steps()
        task = self.workflow.get_tasks(TaskState.READY)[0]
        self.workflow.complete_task_from_id(task.id)
        self.workflow.do_engine_steps()
        task = self.workflow.get_tasks(TaskState.READY)[0]
        self.assertEqual('UserTaskTwo', task.get_name())

        # Send cancel notifications to the workflow
        self.workflow.catch(SignalEventDefinition('cancel'))  # generate a cancel signal.
        self.workflow.catch(CancelEventDefinition())
        self.workflow.do_engine_steps()

        # The cancel event shave h
        self.assertEqual("cancel_event", self.workflow.last_task.data['cancel'])


def suite():
    return unittest.TestLoader().loadTestsFromTestCase(MultipleEventsTest)
if __name__ == '__main__':
    unittest.TextTestRunner(verbosity=2).run(suite())

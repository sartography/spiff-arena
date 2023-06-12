# Copyright (C) 2023 Sartography
#
# This file is part of SpiffWorkflow.
#
# SpiffWorkflow is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 3.0 of the License, or (at your option) any later version.
#
# SpiffWorkflow is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301  USA

from SpiffWorkflow.bpmn.specs.event_definitions import MessageEventDefinition

class MessageEventDefinition(MessageEventDefinition):
    """
    Message Events have both a name and a payload.
    """

    # It is not entirely clear how the payload is supposed to be handled, so I have
    # deviated from what the earlier code did as little as possible, but I believe
    # this should be revisited: for one thing, we're relying on some Camunda-specific
    # properties.

    def __init__(self, name, correlation_properties=None, payload=None, result_var=None, **kwargs):

        super(MessageEventDefinition, self).__init__(name, correlation_properties, **kwargs)
        self.payload = payload
        self.result_var = result_var

        # The BPMN spec says that Messages should not be used within a process; however
        # our camunda workflows depend on it
        self.internal = True

    def throw(self, my_task):
        # We need to evaluate the message payload in the context of this task
        result = my_task.workflow.script_engine.evaluate(my_task, self.payload)
        # We can't update our own payload, because if this task is reached again
        # we have to evaluate it again so we have to create a new event
        event = MessageEventDefinition(self.name, payload=result, result_var=self.result_var)
        self._throw(event, my_task.workflow, my_task.workflow.outer_workflow)

    def update_internal_data(self, my_task, event_definition):
        if event_definition.result_var is None:
            result_var = f'{my_task.task_spec.name}_Response'
        else:
            result_var = event_definition.result_var
        # Prevent this from conflicting 
        my_task.internal_data[self.name] = {
            'payload': event_definition.payload,
            'result_var': result_var
        }

    def update_task_data(self, my_task):
        event_data = my_task.internal_data.get(self.name)
        my_task.data[event_data['result_var']] = event_data['payload']

    def reset(self, my_task):
        my_task.internal_data.pop('result_var', None)
        super(MessageEventDefinition, self).reset(my_task)

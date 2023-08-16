from copy import deepcopy

from SpiffWorkflow.exceptions import WorkflowException
from SpiffWorkflow.bpmn.event import BpmnEvent, PendingBpmnEvent
from .base import EventDefinition

class CorrelationProperty:
    """Rules for generating a correlation key when a message is sent or received."""

    def __init__(self, name, retrieval_expression, correlation_keys):
        self.name = name                                    # This is the property name
        self.retrieval_expression = retrieval_expression    # This is how it's generated
        self.correlation_keys = correlation_keys            # These are the keys it's used by


class MessageEventDefinition(EventDefinition):
    """The default message event."""

    def __init__(self, name, correlation_properties=None, **kwargs):
        super().__init__(name, **kwargs)
        self.correlation_properties = correlation_properties or []

    def catches(self, my_task, event):
        correlations = my_task.workflow.correlations
        if len(self.correlation_properties) == 0 or not correlations:
            # If we are not checking correlations (eg in lots of older workflows) OR this is the first message this is True
            correlated = True
        else:
            # Otherwise we have to check to make sure any existing keys match
            correlated = all([event.correlations.get(key) == correlations.get(key) for key in event.correlations ])
        return self == event.event_definition and correlated

    def catch(self, my_task, event=None):
        self.update_internal_data(my_task, event)
        super().catch(my_task, event)

    def throw(self, my_task):
        payload = deepcopy(my_task.data)
        correlations = self.get_correlations(my_task, payload)
        my_task.workflow.correlations.update(correlations)
        event = BpmnEvent(self, payload=payload, correlations=correlations)
        my_task.workflow.top_workflow.catch(event)

    def update_internal_data(self, my_task, event):
        my_task.internal_data[event.event_definition.name] = event.payload

    def update_task_data(self, my_task):
        # I've added this method so that different message implementations can handle
        # copying their message data into the task
        payload = my_task.internal_data.get(self.name)
        if payload is not None:
            my_task.set_data(**payload)

    def get_correlations(self, task, payload):
        correlations = {}
        for property in self.correlation_properties:
            for key in property.correlation_keys:
                if key not in correlations:
                    correlations[key] = {}
                try:
                    correlations[key][property.name] = task.workflow.script_engine._evaluate(property.retrieval_expression, payload)
                except WorkflowException:
                    # Just ignore missing keys.  The dictionaries have to match exactly
                    pass
        return correlations

    def details(self, my_task):
        return PendingBpmnEvent(self.name, self.__class__.__name__, self.correlation_properties)

    def __eq__(self, other):
        return super().__eq__(other) and self.name == other.name
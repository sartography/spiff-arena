"""Custom_parser."""
from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore

from spiffworkflow_backend.specs.start_event import StartEvent


class MyCustomParser(BpmnDmnParser):  # type: ignore
    """A BPMN and DMN parser that can also parse spiffworkflow-specific extensions."""

    OVERRIDE_PARSER_CLASSES = {}
    OVERRIDE_PARSER_CLASSES.update(BpmnDmnParser.OVERRIDE_PARSER_CLASSES)
    OVERRIDE_PARSER_CLASSES.update(SpiffBpmnParser.OVERRIDE_PARSER_CLASSES)

    StartEvent.register_parser_class(OVERRIDE_PARSER_CLASSES)

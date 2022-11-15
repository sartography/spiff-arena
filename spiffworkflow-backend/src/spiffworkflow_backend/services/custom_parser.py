"""Custom_parser."""
from SpiffWorkflow.dmn.parser.BpmnDmnParser import BpmnDmnParser  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore


class MyCustomParser(BpmnDmnParser):  # type: ignore
    """A BPMN and DMN parser that can also parse spiffworkflow-specific extensions."""

    OVERRIDE_PARSER_CLASSES = BpmnDmnParser.OVERRIDE_PARSER_CLASSES
    OVERRIDE_PARSER_CLASSES.update(SpiffBpmnParser.OVERRIDE_PARSER_CLASSES)

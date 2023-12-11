from typing import Any

from SpiffWorkflow.bpmn.parser.BpmnParser import full_tag  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore
from SpiffWorkflow.spiff.parser.task_spec import ServiceTaskParser  # type: ignore

from spiffworkflow_backend.data_stores import register_data_store_classes
from spiffworkflow_backend.services.service_task_service import CustomServiceTask
from spiffworkflow_backend.specs.start_event import StartEvent


class MyCustomParser(SpiffBpmnParser):  # type: ignore
    """A BPMN and DMN parser that can also parse spiffworkflow-backend specific extensions."""

    OVERRIDE_PARSER_CLASSES = SpiffBpmnParser.OVERRIDE_PARSER_CLASSES
    OVERRIDE_PARSER_CLASSES.update({full_tag("serviceTask"): (ServiceTaskParser, CustomServiceTask)})

    StartEvent.register_parser_class(OVERRIDE_PARSER_CLASSES)

    DATA_STORE_CLASSES: dict[str, Any] = {}

    register_data_store_classes(DATA_STORE_CLASSES)

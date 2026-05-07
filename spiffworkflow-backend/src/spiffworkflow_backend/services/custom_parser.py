import contextlib
from typing import Any
from typing import cast

from SpiffWorkflow.bpmn.parser.BpmnParser import full_tag  # type: ignore
from SpiffWorkflow.bpmn.parser.util import xpath_eval  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore
from SpiffWorkflow.spiff.parser.task_spec import ServiceTaskParser  # type: ignore

from spiffworkflow_backend.data_stores import register_data_store_classes
from spiffworkflow_backend.services.custom_service_task import CustomServiceTask
from spiffworkflow_backend.specs.start_event import StartEvent

SPIFFWORKFLOW_NSMAP = {"spiffworkflow": "http://spiffworkflow.org/bpmn/schema/1.0/core"}


class CustomServiceTaskParser(ServiceTaskParser):  # type: ignore[misc]
    def create_task(self) -> CustomServiceTask:
        extensions = self.parse_extensions()
        operator = extensions.get("serviceTaskOperator")
        prescript = extensions.get("preScript")
        postscript = extensions.get("postScript")

        retries = None
        xpath = xpath_eval(self.node, SPIFFWORKFLOW_NSMAP)
        retry_elements = xpath("./bpmn:extensionElements/spiffworkflow:serviceTaskOperator/spiffworkflow:retry")
        if retry_elements:
            retries_val = retry_elements[0].get("retries")
            if retries_val:
                with contextlib.suppress(ValueError):
                    retries = int(retries_val)

        return cast(
            CustomServiceTask,
            self.spec_class(
                self.spec,
                self.bpmn_id,
                operation_name=operator["name"],
                operation_params=operator["parameters"],
                result_variable=operator["resultVariable"],
                prescript=prescript,
                postscript=postscript,
                retries=retries,
                **self.bpmn_attributes,
            ),
        )


class MyCustomParser(SpiffBpmnParser):  # type: ignore
    """A BPMN and DMN parser that can also parse spiffworkflow-backend specific extensions."""

    OVERRIDE_PARSER_CLASSES = SpiffBpmnParser.OVERRIDE_PARSER_CLASSES
    OVERRIDE_PARSER_CLASSES.update({full_tag("serviceTask"): (CustomServiceTaskParser, CustomServiceTask)})

    StartEvent.register_parser_class(OVERRIDE_PARSER_CLASSES)

    DATA_STORE_CLASSES: dict[str, Any] = {}

    register_data_store_classes(DATA_STORE_CLASSES)

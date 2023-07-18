"""APIs for dealing with process groups, process models, and process instances."""
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.routes.process_instances_controller import process_instance_start

def get_onboarding() -> Response:
    process_instance, processor = process_instance_start("misc/jonjon/onboarding1")
    workflow_data = {}
    
    if processor is not None and process_instance.status == "complete":
        workflow_data = processor.bpmn_process_instance.data
    
    return make_response(workflow_data.get("onboarding", {}), 200)

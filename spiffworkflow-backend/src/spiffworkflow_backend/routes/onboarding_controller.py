"""APIs for dealing with process groups, process models, and process instances."""
from flask import make_response
from flask.wrappers import Response


def get_onboarding() -> Response:
    # TODO: this is an example of what would result from running an optional workflow to determine
    # what onboarding to show
    workflow_data = {
        "x": 1,
        "some_name": "bob",
        "onboarding": {
            "type": "default_view",
            "value": "my_tasks",
        },
    }
    
    return make_response(workflow_data.get("onboarding", {}), 200)

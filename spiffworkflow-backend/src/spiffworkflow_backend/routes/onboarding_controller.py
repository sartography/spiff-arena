"""APIs for dealing with process groups, process models, and process instances."""
from flask import make_response
from flask.wrappers import Response


def get_onboarding() -> Response:
    return make_response({}, 200)

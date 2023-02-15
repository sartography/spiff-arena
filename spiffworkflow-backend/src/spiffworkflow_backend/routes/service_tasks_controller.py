"""APIs for dealing with process groups, process models, and process instances."""
import json

import flask.wrappers
import werkzeug
from flask import current_app
from flask import g
from flask import redirect
from flask import request
from flask.wrappers import Response

from spiffworkflow_backend.routes.user import verify_token
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.service_task_service import ServiceTaskService


def service_task_list() -> flask.wrappers.Response:
    """Service_task_list."""
    available_connectors = ServiceTaskService.available_connectors()
    return Response(
        json.dumps(available_connectors), status=200, mimetype="application/json"
    )


def authentication_list() -> flask.wrappers.Response:
    """Authentication_list."""
    available_authentications = ServiceTaskService.authentication_list()
    response_json = {
        "results": available_authentications,
        "connector_proxy_base_url": current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL"],
        "redirect_url": f"{current_app.config['SPIFFWORKFLOW_BACKEND_URL']}/v1.0/authentication_callback",
    }

    return Response(json.dumps(response_json), status=200, mimetype="application/json")


def authentication_callback(
    service: str,
    auth_method: str,
) -> werkzeug.wrappers.Response:
    """Authentication_callback."""
    verify_token(request.args.get("token"), force_run=True)
    response = request.args["response"]
    SecretService().update_secret(
        f"{service}/{auth_method}", response, g.user.id, create_if_not_exists=True
    )
    return redirect(
        f"{current_app.config['SPIFFWORKFLOW_BACKEND_SPIFFWORKFLOW_FRONTEND_URL']}/admin/configuration"
    )

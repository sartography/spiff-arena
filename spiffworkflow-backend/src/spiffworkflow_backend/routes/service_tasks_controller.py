"""APIs for dealing with process groups, process models, and process instances."""

import json

import flask.wrappers
import werkzeug
from flask import current_app
from flask import g
from flask import redirect
from flask import request
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.authentication_controller import verify_token
from spiffworkflow_backend.services.oauth_service import OAuthService
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.service_task_service import ServiceTaskService


def service_task_list() -> flask.wrappers.Response:
    available_connectors = ServiceTaskService.available_connectors()
    return Response(json.dumps(available_connectors), status=200, mimetype="application/json")


def authentication_list() -> flask.wrappers.Response:
    available_authentications = ServiceTaskService.authentication_list()
    available_v2_authentications = OAuthService.authentication_list()

    response_json = {
        "results": available_authentications,
        "resultsV2": available_v2_authentications,
        "connector_proxy_base_url": current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL"],
        "redirect_url": f"{current_app.config['SPIFFWORKFLOW_BACKEND_URL']}/v1.0/authentication_callback",
    }

    return Response(json.dumps(response_json), status=200, mimetype="application/json")


def authentication_configuration() -> flask.wrappers.Response:
    config = OAuthService.authentication_configuration()

    return Response(json.dumps(config), status=200, mimetype="application/json")


def authentication_configuration_update(body: dict) -> flask.wrappers.Response:
    OAuthService.update_authentication_configuration(body)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def authentication_begin(
    service: str,
    auth_method: str,
) -> werkzeug.wrappers.Response:
    token = request.args.get("token")
    verify_token(token, force_run=True)
    if not OAuthService.supported_service(service):
        raise ApiError("unknown_authentication_service", f"Unknown authentication service: {service}", status_code=400)
    remote_app = OAuthService.remote_app(service, token)
    callback = f"{current_app.config['SPIFFWORKFLOW_BACKEND_URL']}/v1.0/authentication_callback/{service}/oauth"
    return remote_app.authorize(callback=callback, _external=True)  # type: ignore


def authentication_callback(
    service: str,
    auth_method: str,
) -> werkzeug.wrappers.Response:
    if OAuthService.supported_service(service):
        token = OAuthService.token_from_state(request.args.get("state"))
        verify_token(token, force_run=True)
        remote_app = OAuthService.remote_app(service, token)
        response = remote_app.authorized_response()
        SecretService.update_secret(f"{service}_{auth_method}", response["access_token"], g.user.id, create_if_not_exists=True)
    else:
        verify_token(request.args.get("token"), force_run=True)
        response = request.args["response"]
        SecretService.update_secret(f"{service}/{auth_method}", response, g.user.id, create_if_not_exists=True)
    return redirect(f"{current_app.config['SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND']}/configuration")

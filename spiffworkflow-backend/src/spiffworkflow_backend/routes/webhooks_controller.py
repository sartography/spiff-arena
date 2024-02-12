import json

from flask import current_app
from flask import request
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model_for_instantiation
from spiffworkflow_backend.routes.process_api_blueprint import _un_modify_modified_process_model_id
from spiffworkflow_backend.services.authentication_service import AuthenticationService  # noqa: F401
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


# sample body:
# {"ref": "refs/heads/main", "repository": {"name": "sample-process-models",
# "full_name": "sartography/sample-process-models", "private": False .... }}
# test with: ngrok http 7000
# or with:
# npm install -g localtunnel && lt --port 7000 --subdomain oh-so-hot
# where 7000 is the port the app is running on locally
# so this would work: curl https://oh-so-hot.loca.lt/v1.0/status
def github_webhook_receive(body: dict) -> Response:
    _enforce_github_auth()
    result = GitService.handle_web_hook(body)
    return Response(json.dumps({"git_pull": result}), status=200, mimetype="application/json")


def webhook(body: dict) -> Response:
    if current_app.config["SPIFFWORKFLOW_BACKEND_WEBHOOK_ENFORCES_GITHUB_AUTH"] is True:
        _enforce_github_auth()

    if current_app.config["SPIFFWORKFLOW_BACKEND_WEBHOOK_PROCESS_MODEL_IDENTIFIER"] is None:
        error_message = "Webhook process model implementation not configured"
        raise ApiError(
            error_code="webhook_not_configured",
            message=error_message,
            status_code=501,
        )

    process_model = _get_process_model_for_instantiation(
        _un_modify_modified_process_model_id(current_app.config["SPIFFWORKFLOW_BACKEND_WEBHOOK_PROCESS_MODEL_IDENTIFIER"])
    )
    ProcessInstanceService.create_and_run_process_instance(
        process_model=process_model,
        persistence_level="none",
        data_to_inject={"headers": dict(request.headers), "body": body},
    )

    # ensure we commit the message instances
    db.session.commit()

    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def _enforce_github_auth() -> None:
    auth_header = request.headers.get("X-Hub-Signature-256")
    AuthenticationService.verify_sha256_token(auth_header)

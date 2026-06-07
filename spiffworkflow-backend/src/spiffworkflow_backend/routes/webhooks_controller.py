from hashlib import sha256
from hmac import HMAC
from hmac import compare_digest

import requests
from flask import current_app
from flask import jsonify
from flask import make_response
from flask import request
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model_for_instantiation
from spiffworkflow_backend.services.authentication_service import AuthenticationService  # noqa: F401
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_import_service import ProcessModelImportService


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
    return make_response(jsonify({"git_pull": result}), 200)


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
        ProcessModelInfo.unmodify_process_identifier_from_path_param(
            current_app.config["SPIFFWORKFLOW_BACKEND_WEBHOOK_PROCESS_MODEL_IDENTIFIER"]
        )
    )
    ProcessInstanceService.create_and_run_process_instance(
        process_model=process_model,
        persistence_level="none",
        data_to_inject={"headers": dict(request.headers), "body": body},
    )

    # ensure we commit the message instances
    db.session.commit()

    return make_response(jsonify({"ok": True}), 200)


def filestore_webhook(body: dict) -> Response:
    _enforce_filestore_auth()

    if body.get("event") != "snapshot.created":
        return make_response(jsonify({"ok": True, "process_models": []}), 200)

    package = body.get("package")
    if package is None:
        arena_package_url = body.get("arena_package_url")
        if not arena_package_url:
            raise ApiError(
                error_code="missing_arena_package_url",
                message="Filestore snapshot webhook must include arena_package_url or package",
                status_code=400,
            )
        response = requests.get(arena_package_url, headers=_filestore_headers(body), timeout=30)
        if response.status_code != 200:
            raise ApiError(
                error_code="filestore_package_fetch_failed",
                message=f"Could not fetch Files arena package: {response.status_code}",
                status_code=502,
            )
        package = response.json()

    process_group_id = body.get("process_group_id") or current_app.config["SPIFFWORKFLOW_BACKEND_FILESTORE_PROCESS_GROUP_ID"]
    process_models = ProcessModelImportService.import_from_filestore_package(package, process_group_id)
    GitService.commit_on_save(
        f"Imported Files project {package.get('project_id')} snapshot {package.get('snapshot_id')} into {process_group_id}"
    )

    return make_response(
        jsonify({
            "ok": True,
            "process_models": [process_model.to_dict() for process_model in process_models],
        }),
        200,
    )


def _filestore_headers(body: dict) -> dict[str, str]:
    tenant_id = body.get("tenant_id")
    return {"SpiffWorkflow-Tenant": str(tenant_id)} if tenant_id else {}


def _enforce_filestore_auth() -> None:
    secret = current_app.config.get("SPIFFWORKFLOW_BACKEND_FILESTORE_WEBHOOK_SECRET")
    if not secret:
        return

    auth_header = request.headers.get("SpiffWorkflow-Signature")
    if not auth_header:
        raise ApiError(error_code="unauthorized", message="unauthorized", status_code=401)

    received_sign = auth_header.split("sha256=")[-1].strip()
    expected_sign = HMAC(key=secret.encode(), msg=request.data, digestmod=sha256).hexdigest()
    if not compare_digest(received_sign, expected_sign):
        raise ApiError(error_code="unauthorized", message="unauthorized", status_code=401)


def _enforce_github_auth() -> None:
    auth_header = request.headers.get("X-Hub-Signature-256")
    AuthenticationService.verify_sha256_token(auth_header)

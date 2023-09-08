import json
import os
from spiffworkflow_backend.models.db import db
import re
from hashlib import sha256
from typing import Any

import connexion  # type: ignore
import flask.wrappers
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def service_account_create(
    body: dict[str, Any]
) -> flask.wrappers.Response:
    api_key_name = body["name"]
    service_account = ServiceAccountModel.query.filter(created_by_user_id=g.user.id, name=api_key_name).first()

    if service_account is not None:
        raise ApiError(
            error_code="service_account_already_exists",
            message=(
                f"Service account with name '{api_key_name}' for user '{g.user.username}' already exists."
                " Please specify a different name."
            ),
            status_code=400,
        )
    _create_service_account(api_key_name, g.user.id)
    return make_response(json.dumps({"ok": True}), 201)


def _create_service_account(name: str, created_by_user_id: int) -> ServiceAccountModel:
    api_key =ServiceAccountModel.generate_api_key()
    service_account = ServiceAccountModel(
        name=name,
        created_by_user_id=created_by_user_id,
        api_key=api_key
    )
    db.session.add(service_account)
    _associated_service_account_with_permissions(service_account)
    ServiceAccountModel.commit_with_rollback_on_exception()
    return service_account

def _associated_service_account_with_permissions(service_account: ServiceAccountModel) -> None:
    principal = PrincipalModel.create_principal(service_account.id, "service_account_id")

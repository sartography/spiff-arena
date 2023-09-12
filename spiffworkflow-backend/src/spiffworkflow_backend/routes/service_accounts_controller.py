from typing import Any

import flask.wrappers
from flask import g
from flask import make_response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.services.service_account_service import ServiceAccountService


def service_account_create(body: dict[str, Any]) -> flask.wrappers.Response:
    api_key_name = body["name"]
    service_account = ServiceAccountModel.query.filter_by(created_by_user_id=g.user.id, name=api_key_name).first()

    if service_account is not None:
        raise ApiError(
            error_code="service_account_already_exists",
            message=(
                f"Service account with name '{api_key_name}' for user '{g.user.username}' already exists."
                " Please specify a different name."
            ),
            status_code=400,
        )
    service_account = ServiceAccountService.create_service_account(api_key_name, g.user)
    return make_response({"api_key": service_account.api_key}, 201)

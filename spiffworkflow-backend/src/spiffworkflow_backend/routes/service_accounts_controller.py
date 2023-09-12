from typing import Any
from spiffworkflow_backend.models.user import UserModel

import flask.wrappers
from flask import g
from flask import make_response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.services.user_service import UserService


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
    service_account = _create_service_account(api_key_name, g.user.id)
    return make_response({"api_key": service_account.api_key}, 201)


def _create_service_account(name: str, created_by_user_id: int) -> ServiceAccountModel:
    api_key = ServiceAccountModel.generate_api_key()
    username=f"{name}_{created_by_user_id}"
    user = UserModel(
        username=username,
        email=f"{username}@spiff.service.account.example.com",
        service="spiff_service_account",
        service_id=f"{username}_service_account",
    )
    db.session.add(user)
    service_account = ServiceAccountModel(name=name, created_by_user_id=created_by_user_id, api_key=api_key, user=user)
    db.session.add(service_account)
    ServiceAccountModel.commit_with_rollback_on_exception()
    _associated_service_account_with_permissions(user)
    return service_account


def _associated_service_account_with_permissions(user: UserModel) -> None:
    principal = UserService.create_principal(user.id, "service_account_id")
    user_permissions = sorted(UserService.get_permission_targets_for_user(g.user))

    permission_objects = []
    for user_permission in user_permissions:
        permission_objects.append(
            PermissionAssignmentModel(
                principal_id=principal.id,
                permission_target_id=user_permission[0],
                permission=user_permission[1],
                grant_type=user_permission[2],
            )
        )

    db.session.bulk_save_objects(permission_objects)
    ServiceAccountModel.commit_with_rollback_on_exception()

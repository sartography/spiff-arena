"""APIs for dealing with process groups, process models, and process instances."""
import json

from flask import g
from flask import jsonify
from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.models.secret_model import SecretModel
from spiffworkflow_backend.models.secret_model import SecretModelSchema
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.secret_service import SecretService
from spiffworkflow_backend.services.user_service import UserService


def secret_show(key: str) -> Response:
    """Secret_show."""
    secret = SecretService.get_secret(key)
    return make_response(jsonify(secret), 200)


def secret_list(
    page: int = 1,
    per_page: int = 100,
) -> Response:
    """Secret_list."""
    secrets = (
        SecretModel.query.order_by(SecretModel.key)
        .join(UserModel)
        .add_columns(
            UserModel.username,
        )
        .paginate(page=page, per_page=per_page, error_out=False)
    )
    response_json = {
        "results": secrets.items,
        "pagination": {
            "count": len(secrets.items),
            "total": secrets.total,
            "pages": secrets.pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def secret_create(body: dict) -> Response:
    """Add secret."""
    secret_model = SecretService().add_secret(body["key"], body["value"], g.user.id)
    return Response(
        json.dumps(SecretModelSchema().dump(secret_model)),
        status=201,
        mimetype="application/json",
    )


def secret_update(key: str, body: dict) -> Response:
    """Update secret."""
    SecretService().update_secret(key, body["value"], g.user.id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")


def secret_delete(key: str) -> Response:
    """Delete secret."""
    current_user = UserService.current_user()
    SecretService.delete_secret(key, current_user.id)
    return Response(json.dumps({"ok": True}), status=200, mimetype="application/json")

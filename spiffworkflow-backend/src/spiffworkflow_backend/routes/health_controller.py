from flask import current_app
from flask import g, make_response
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService


def status() -> Response:
    ProcessInstanceModel.query.filter().first()

    # Default to allowing frontend access
    can_access_frontend = True

    # Check if user is logged in and if they have access to the frontend
    current_app.logger.warn("checking")
    if hasattr(g, "user"):
        current_app.logger.warn("got user")

        can_access_frontend = AuthorizationService.user_has_permission(
            user=g.user, permission="read", target_uri="/frontend-access"
        )
        current_app.logger.warn("can_access_frontend")
        current_app.logger.warn(can_access_frontend)

    return make_response({"ok": True, "can_access_frontend": can_access_frontend}, 200)

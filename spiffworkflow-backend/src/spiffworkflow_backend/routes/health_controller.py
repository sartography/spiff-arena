from flask import make_response
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.authentication_service import AuthenticationService
from spiffworkflow_backend.services.authorization_service import AuthorizationService


def status() -> Response:
    ProcessInstanceModel.query.filter().first()

    # Default to allowing frontend access
    can_access_frontend = True

    # Try to get the user from token in the request
    user = AuthenticationService.get_current_user_from_request()
    if user is not None:
        can_access_frontend = AuthorizationService.user_has_permission(
            user=user, permission="read", target_uri="/frontend-access"
        )

    return make_response({"ok": True, "can_access_frontend": can_access_frontend}, 200)

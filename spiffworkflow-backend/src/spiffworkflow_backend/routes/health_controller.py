from flask import current_app, make_response
from flask.wrappers import Response

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.routes.authentication_controller import _find_token_from_request, _get_decoded_token, _get_user_model_from_token
from spiffworkflow_backend.services.authorization_service import AuthorizationService


def status() -> Response:
    ProcessInstanceModel.query.filter().first()

    # Default to allowing frontend access
    can_access_frontend = True

    # Try to get the user from token in the request
    try:
        token_info = _find_token_from_request(None)
        if token_info["token"] is not None:
            decoded_token = _get_decoded_token(token_info["token"])
            user = _get_user_model_from_token(decoded_token)
            if user is not None:
                can_access_frontend = AuthorizationService.user_has_permission(
                    user=user, permission="read", target_uri="/frontend-access"
                )
    except Exception as e:
        current_app.logger.warning(f"Error checking frontend access: {str(e)}")
        # If there's any error, default to allowing access
        can_access_frontend = True

    return make_response({"ok": True, "can_access_frontend": can_access_frontend}, 200)

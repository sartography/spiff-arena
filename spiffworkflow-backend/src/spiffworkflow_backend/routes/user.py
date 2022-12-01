"""User."""
import ast
import base64
import json
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import jwt
from flask import current_app
from flask import g
from flask import redirect
from flask import request
from flask_bpmn.api.api_error import ApiError
from werkzeug.wrappers import Response

from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authentication_service import (
    AuthenticationService,
)
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.user_service import UserService

"""
.. module:: crc.api.user
   :synopsis: Single Sign On (SSO) user login and session handlers
"""


# authorization_exclusion_list = ['status']
def verify_token(
    token: Optional[str] = None, force_run: Optional[bool] = False
) -> Optional[Dict[str, Optional[Union[str, int]]]]:
    """Verify the token for the user (if provided).

    If in production environment and token is not provided, gets user from the SSO headers and returns their token.

    Args:
        token: Optional[str]
        force_run: Optional[bool]

    Returns:
        token: str

    Raises:  # noqa: DAR401
        ApiError:  If not on production and token is not valid, returns an 'invalid_token' 403 error.
        If on production and user is not authenticated, returns a 'no_user' 403 error.
    """
    user_info = None
    if not force_run and AuthorizationService.should_disable_auth_for_request():
        return None

    if not token and "Authorization" in request.headers:
        token = request.headers["Authorization"].removeprefix("Bearer ")

    if token:
        user_model = None
        decoded_token = get_decoded_token(token)

        if decoded_token is not None:
            if "token_type" in decoded_token:
                token_type = decoded_token["token_type"]
                if token_type == "internal":  # noqa: S105
                    try:
                        user_model = get_user_from_decoded_internal_token(decoded_token)
                    except Exception as e:
                        current_app.logger.error(
                            f"Exception in verify_token getting user from decoded internal token. {e}"
                        )
            elif "iss" in decoded_token.keys():
                try:
                    if AuthenticationService.validate_id_token(token):
                        user_info = decoded_token
                except ApiError as ae:  # API Error is only thrown in the token is outdated.
                    # Try to refresh the token
                    user = UserService.get_user_by_service_and_service_id(
                        "open_id", decoded_token["sub"]
                    )
                    if user:
                        refresh_token = AuthenticationService.get_refresh_token(user.id)
                        if refresh_token:
                            auth_token: dict = (
                                AuthenticationService.get_auth_token_from_refresh_token(
                                    refresh_token
                                )
                            )
                            if auth_token and "error" not in auth_token:
                                # We have the user, but this code is a bit convoluted, and will later demand
                                # a user_info object so it can look up the user.  Sorry to leave this crap here.
                                user_info = {"sub": user.service_id}
                            else:
                                raise ae
                        else:
                            raise ae
                    else:
                        raise ae
                except Exception as e:
                    current_app.logger.error(f"Exception raised in get_token: {e}")
                    raise ApiError(
                        error_code="fail_get_user_info",
                        message="Cannot get user info from token",
                        status_code=401,
                    ) from e

                if (
                    user_info is not None and "error" not in user_info
                ):  # not sure what to test yet
                    user_model = (
                        UserModel.query.filter(UserModel.service == "open_id")
                        .filter(UserModel.service_id == user_info["sub"])
                        .first()
                    )
                    if user_model is None:
                        raise ApiError(
                            error_code="invalid_user",
                            message="Invalid user. Please log in.",
                            status_code=401,
                        )
                # no user_info
                else:
                    raise ApiError(
                        error_code="no_user_info",
                        message="Cannot retrieve user info",
                        status_code=401,
                    )

            else:
                current_app.logger.debug(
                    "token_type not in decode_token in verify_token"
                )
                raise ApiError(
                    error_code="invalid_token",
                    message="Invalid token. Please log in.",
                    status_code=401,
                )

        if user_model:
            g.user = user_model

        # If the user is valid, store the token for this session
        if g.user:
            # This is an id token, so we don't have a refresh token yet
            g.token = token
            get_scope(token)
            return None
            # return {"uid": g.user.id, "sub": g.user.id, "scope": scope}
            # return validate_scope(token, user_info, user_model)
        else:
            raise ApiError(error_code="no_user_id", message="Cannot get a user id")

    raise ApiError(
        error_code="invalid_token", message="Cannot validate token.", status_code=401
    )


def validate_scope(token: Any) -> bool:
    """Validate_scope."""
    print("validate_scope")
    # token = AuthenticationService.refresh_token(token)
    # user_info = AuthenticationService.get_user_info_from_public_access_token(token)
    # bearer_token = AuthenticationService.get_bearer_token(token)
    # permission = AuthenticationService.get_permission_by_basic_token(token)
    # permissions = AuthenticationService.get_permissions_by_token_for_resource_and_scope(token)
    # introspection = AuthenticationService.introspect_token(basic_token)
    return True


def encode_auth_token(sub: str, token_type: Optional[str] = None) -> str:
    """Generates the Auth Token.

    :return: string
    """
    payload = {"sub": sub}
    if token_type is None:
        token_type = "internal"  # noqa: S105
    payload["token_type"] = token_type
    if "SECRET_KEY" in current_app.config:
        secret_key = current_app.config.get("SECRET_KEY")
    else:
        current_app.logger.error("Missing SECRET_KEY in encode_auth_token")
        raise ApiError(
            error_code="encode_error", message="Missing SECRET_KEY in encode_auth_token"
        )
    return jwt.encode(
        payload,
        str(secret_key),
        algorithm="HS256",
    )


def login(redirect_url: str = "/") -> Response:
    """Login."""
    state = AuthenticationService.generate_state(redirect_url)
    login_redirect_url = AuthenticationService().get_login_redirect_url(
        state.decode("UTF-8")
    )
    return redirect(login_redirect_url)


def parse_id_token(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        raise Exception("Incorrect id token format")

    payload = parts[1]
    padded = payload + "=" * (4 - len(payload) % 4)
    decoded = base64.b64decode(padded)
    return json.loads(decoded)


def login_return(code: str, state: str, session_state: str) -> Optional[Response]:
    """Login_return."""
    state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))
    state_redirect_url = state_dict["redirect_url"]
    auth_token_object = AuthenticationService().get_auth_token_object(code)
    if "id_token" in auth_token_object:
        id_token = auth_token_object["id_token"]

        user_info = parse_id_token(id_token)

        if AuthenticationService.validate_id_token(id_token):
            if user_info and "error" not in user_info:
                user_model = AuthorizationService.create_user_from_sign_in(user_info)
                g.user = user_model.id
                g.token = auth_token_object["id_token"]
                AuthenticationService.store_refresh_token(
                    user_model.id, auth_token_object["refresh_token"]
                )
                redirect_url = (
                    f"{state_redirect_url}?"
                    + f"access_token={auth_token_object['access_token']}&"
                    + f"id_token={id_token}"
                )
                return redirect(redirect_url)

        raise ApiError(
            error_code="invalid_login",
            message="Login failed. Please try again",
            status_code=401,
        )

    else:
        raise ApiError(
            error_code="invalid_token",
            message="Login failed. Please try again",
            status_code=401,
        )


def login_api() -> Response:
    """Login_api."""
    redirect_url = "/v1.0/login_api_return"
    state = AuthenticationService.generate_state(redirect_url)
    login_redirect_url = AuthenticationService().get_login_redirect_url(
        state.decode("UTF-8"), redirect_url
    )
    return redirect(login_redirect_url)


def login_api_return(code: str, state: str, session_state: str) -> str:
    """Login_api_return."""
    state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))
    state_dict["redirect_url"]

    auth_token_object = AuthenticationService().get_auth_token_object(
        code, "/v1.0/login_api_return"
    )
    access_token: str = auth_token_object["access_token"]
    assert access_token  # noqa: S101
    return access_token
    # return redirect("localhost:7000/v1.0/ui")
    # return {'uid': 'user_1'}


def logout(id_token: str, redirect_url: Optional[str]) -> Response:
    """Logout."""
    if redirect_url is None:
        redirect_url = ""
    return AuthenticationService().logout(redirect_url=redirect_url, id_token=id_token)


def logout_return() -> Response:
    """Logout_return."""
    frontend_url = str(current_app.config["SPIFFWORKFLOW_FRONTEND_URL"])
    return redirect(f"{frontend_url}/")


def get_decoded_token(token: str) -> Optional[Dict]:
    """Get_token_type."""
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        print(f"Exception in get_token_type: {e}")
        raise ApiError(
            error_code="invalid_token", message="Cannot decode token."
        ) from e
    else:
        if "token_type" in decoded_token or "iss" in decoded_token:
            return decoded_token
        else:
            current_app.logger.error(
                f"Unknown token type in get_decoded_token: token: {token}"
            )
            raise ApiError(
                error_code="unknown_token",
                message="Unknown token type in get_decoded_token",
            )
    # try:
    #     # see if we have an open_id token
    #     decoded_token = AuthorizationService.decode_auth_token(token)
    # else:
    #     if 'sub' in decoded_token and 'iss' in decoded_token and 'aud' in decoded_token:
    #         token_type = 'id_token'

    # if 'token_type' in decoded_token and 'sub' in decoded_token:
    #     return True


def get_scope(token: str) -> str:
    """Get_scope."""
    scope = ""
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    if "scope" in decoded_token:
        scope = decoded_token["scope"]
    return scope


def get_user_from_decoded_internal_token(decoded_token: dict) -> Optional[UserModel]:
    """Get_user_from_decoded_internal_token."""
    sub = decoded_token["sub"]
    parts = sub.split("::")
    service = parts[0].split(":")[1]
    service_id = parts[1].split(":")[1]
    user: UserModel = (
        UserModel.query.filter(UserModel.service == service)
        .filter(UserModel.service_id == service_id)
        .first()
    )
    if user:
        return user
    user = UserModel(
        username=service_id,
        service=service,
        service_id=service_id,
    )
    return user

"""User."""
import ast
import base64
from typing import Any
from typing import Dict
from typing import Optional
from typing import Union

import jwt
from flask import current_app
from flask import g
from flask import redirect
from flask_bpmn.api.api_error import ApiError
from werkzeug.wrappers.response import Response

from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authentication_service import (
    PublicAuthenticationService,
)
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.user_service import UserService

"""
.. module:: crc.api.user
   :synopsis: Single Sign On (SSO) user login and session handlers
"""


def verify_token(token: Optional[str] = None) -> Dict[str, Optional[Union[str, int]]]:
    """Verify the token for the user (if provided).

    If in production environment and token is not provided, gets user from the SSO headers and returns their token.

    Args:
        token: Optional[str]

    Returns:
        token: str

    Raises:  # noqa: DAR401
        ApiError:  If not on production and token is not valid, returns an 'invalid_token' 403 error.
        If on production and user is not authenticated, returns a 'no_user' 403 error.
    """
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
                    user_info = PublicAuthenticationService.get_user_info_from_id_token(
                        token
                    )
                except ApiError as ae:
                    raise ae
                except Exception as e:
                    current_app.logger.error(f"Exception raised in get_token: {e}")
                    raise ApiError(
                        error_code="fail_get_user_info",
                        message="Cannot get user info from token",
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
                        error_code="no_user_info", message="Cannot retrieve user info"
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
            g.token = token
            scope = get_scope(token)
            return {"uid": g.user.id, "sub": g.user.id, "scope": scope}
            # return validate_scope(token, user_info, user_model)
        else:
            raise ApiError(error_code="no_user_id", message="Cannot get a user id")

    raise ApiError(
        error_code="invalid_token", message="Cannot validate token.", status_code=401
    )
    # no token -- do we ever get here?
    # else:
    #     ...
    # if current_app.config.get("DEVELOPMENT"):
    #     # Fall back to a default user if this is not production.
    #     g.user = UserModel.query.first()
    #     if not g.user:
    #         raise ApiError(
    #             "no_user",
    #             "You are in development mode, but there are no users in the database.  Add one, and it will use it.",
    #         )
    #     token_from_user = g.user.encode_auth_token()
    #     token_info = UserModel.decode_auth_token(token_from_user)
    #     return token_info
    #
    # else:
    #     raise ApiError(
    #         error_code="no_auth_token",
    #         message="No authorization token was available.",
    #         status_code=401,
    #     )


def validate_scope(token: Any) -> bool:
    """Validate_scope."""
    print("validate_scope")
    # token = PublicAuthenticationService.refresh_token(token)
    # user_info = PublicAuthenticationService.get_user_info_from_public_access_token(token)
    # bearer_token = PublicAuthenticationService.get_bearer_token(token)
    # permission = PublicAuthenticationService.get_permission_by_basic_token(token)
    # permissions = PublicAuthenticationService.get_permissions_by_token_for_resource_and_scope(token)
    # introspection = PublicAuthenticationService.introspect_token(basic_token)
    return True


# def login_api(redirect_url: str = "/v1.0/ui") -> Response:
#     """Api_login."""
#     # TODO: Fix this! mac 20220801
#     # token:dict = PublicAuthenticationService().get_public_access_token(uid, password)
#     #
#     # return token
#     # if uid:
#     #     sub = f"service:internal::service_id:{uid}"
#     #     token = encode_auth_token(sub)
#     #     user_model = UserModel(username=uid,
#     #                            uid=uid,
#     #                            service='internal',
#     #                            name="API User")
#     #     g.user = user_model
#     #
#     #     g.token = token
#     #     scope = get_scope(token)
#     #     return token
#     #     return {"uid": uid, "sub": uid, "scope": scope}
#     return login(redirect_url)


# def login_api_return(code: str, state: str, session_state: str) -> Optional[Response]:
#     print("login_api_return")


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
    state = PublicAuthenticationService.generate_state(redirect_url)
    login_redirect_url = PublicAuthenticationService().get_login_redirect_url(
        state.decode("UTF-8")
    )
    return redirect(login_redirect_url)


def login_return(code: str, state: str, session_state: str) -> Optional[Response]:
    """Login_return."""
    state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))
    state_redirect_url = state_dict["redirect_url"]

    id_token_object = PublicAuthenticationService().get_id_token_object(code)
    if "id_token" in id_token_object:
        id_token = id_token_object["id_token"]

        if PublicAuthenticationService.validate_id_token(id_token):
            user_info = PublicAuthenticationService.get_user_info_from_id_token(
                id_token_object["access_token"]
            )
            if user_info and "error" not in user_info:
                user_model = (
                    UserModel.query.filter(UserModel.service == "open_id")
                    .filter(UserModel.service_id == user_info["sub"])
                    .first()
                )

                if user_model is None:
                    current_app.logger.debug("create_user in login_return")
                    name = username = email = ""
                    if "name" in user_info:
                        name = user_info["name"]
                    if "username" in user_info:
                        username = user_info["username"]
                    elif "preferred_username" in user_info:
                        username = user_info["preferred_username"]
                    if "email" in user_info:
                        email = user_info["email"]
                    user_model = UserService().create_user(
                        service="open_id",
                        service_id=user_info["sub"],
                        name=name,
                        username=username,
                        email=email,
                    )

                if user_model:
                    g.user = user_model.id

                # this may eventually get too slow.
                # when it does, be careful about backgrounding, because
                # the user will immediately need permissions to use the site.
                # we are also a little apprehensive about pre-creating users
                # before the user signs in, because we won't know things like
                # the external service user identifier.
                AuthorizationService.import_permissions_from_yaml_file()

                redirect_url = (
                    f"{state_redirect_url}?"
                    + f"access_token={id_token_object['access_token']}&"
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
    state = PublicAuthenticationService.generate_state(redirect_url)
    login_redirect_url = PublicAuthenticationService().get_login_redirect_url(
        state.decode("UTF-8"), redirect_url
    )
    return redirect(login_redirect_url)


def login_api_return(code: str, state: str, session_state: str) -> str:
    """Login_api_return."""
    state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))
    state_dict["redirect_url"]

    id_token_object = PublicAuthenticationService().get_id_token_object(
        code, "/v1.0/login_api_return"
    )
    access_token: str = id_token_object["access_token"]
    assert access_token  # noqa: S101
    return access_token
    # return redirect("localhost:7000/v1.0/ui")
    # return {'uid': 'user_1'}


def logout(id_token: str, redirect_url: Optional[str]) -> Response:
    """Logout."""
    if redirect_url is None:
        redirect_url = ""
    return PublicAuthenticationService().logout(
        redirect_url=redirect_url, id_token=id_token
    )


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
    # user: UserModel = UserModel.query.filter()
    if user:
        return user
    user = UserModel(
        username=service_id,
        uid=service_id,
        service=service,
        service_id=service_id,
        name="API User",
    )

    return user

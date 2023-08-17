import ast
import base64
import json
import re
from typing import Any

import flask
import jwt
from flask import current_app
from flask import g
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import request
from werkzeug.wrappers import Response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.api_version import V1_API_PATH_PREFIX
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import SPIFF_NO_AUTH_GROUP
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import SPIFF_ANONYMOUS_USER
from spiffworkflow_backend.models.user import SPIFF_NO_AUTH_USER
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authentication_service import AuthenticationService
from spiffworkflow_backend.services.authentication_service import MissingAccessTokenError
from spiffworkflow_backend.services.authentication_service import TokenExpiredError
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.user_service import UserService

"""
.. module:: crc.api.user
   :synopsis: Single Sign On (SSO) user login and session handlers
"""


# authorization_exclusion_list = ['status']
def verify_token(token: str | None = None, force_run: bool | None = False) -> None:
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

    if not token and "access_token" in request.cookies:
        if request.path.startswith(f"{V1_API_PATH_PREFIX}/process-data-file-download/"):
            token = request.cookies["access_token"]

    # This should never be set here but just in case
    _clear_auth_tokens_from_thread_local_data()

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

                # if the user is the anonymous user and we have auth enabled then make sure we clean up the anonymouse user
                if (
                    user_model
                    and not current_app.config.get("SPIFFWORKFLOW_BACKEND_AUTHENTICATION_DISABLED")
                    and user_model.username == SPIFF_NO_AUTH_USER
                    and user_model.service_id == "spiff_anonymous_service_id"
                ):
                    group_model = GroupModel.query.filter_by(identifier=SPIFF_NO_AUTH_GROUP).first()
                    db.session.delete(group_model)
                    db.session.delete(user_model)
                    db.session.commit()
                    tld = current_app.config["THREAD_LOCAL_DATA"]
                    tld.user_has_logged_out = True
                    return None

            elif "iss" in decoded_token.keys():
                user_info = None
                try:
                    if AuthenticationService.validate_id_or_access_token(token):
                        user_info = decoded_token
                except TokenExpiredError as token_expired_error:
                    # Try to refresh the token
                    user = UserService.get_user_by_service_and_service_id(decoded_token["iss"], decoded_token["sub"])
                    if user:
                        refresh_token = AuthenticationService.get_refresh_token(user.id)
                        if refresh_token:
                            auth_token: dict = AuthenticationService.get_auth_token_from_refresh_token(refresh_token)
                            if auth_token and "error" not in auth_token and "id_token" in auth_token:
                                tld = current_app.config["THREAD_LOCAL_DATA"]
                                tld.new_access_token = auth_token["id_token"]
                                tld.new_id_token = auth_token["id_token"]
                                # We have the user, but this code is a bit convoluted, and will later demand
                                # a user_info object so it can look up the user.  Sorry to leave this crap here.
                                user_info = {
                                    "sub": user.service_id,
                                    "iss": user.service,
                                }

                    if user_info is None:
                        raise ApiError(
                            error_code="invalid_token",
                            message="Your token is expired. Please Login",
                            status_code=401,
                        ) from token_expired_error

                except Exception as e:
                    raise ApiError(
                        error_code="fail_get_user_info",
                        message="Cannot get user info from token",
                        status_code=401,
                    ) from e
                if (
                    user_info is not None and "error" not in user_info and "iss" in user_info
                ):  # not sure what to test yet
                    user_model = (
                        UserModel.query.filter(UserModel.service == user_info["iss"])
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
                current_app.logger.debug("token_type not in decode_token in verify_token")
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
        else:
            raise ApiError(error_code="no_user_id", message="Cannot get a user id")

    raise ApiError(error_code="invalid_token", message="Cannot validate token.", status_code=401)


def set_new_access_token_in_cookie(
    response: flask.wrappers.Response,
) -> flask.wrappers.Response:
    """Checks if a new token has been set in THREAD_LOCAL_DATA and sets cookies if appropriate.

    It will also delete the cookies if the user has logged out.
    """
    tld = current_app.config["THREAD_LOCAL_DATA"]
    domain_for_frontend_cookie: str | None = re.sub(
        r"^https?:\/\/",
        "",
        current_app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"],
    )
    if domain_for_frontend_cookie and domain_for_frontend_cookie.startswith("localhost"):
        domain_for_frontend_cookie = None

    # fixme - we should not be passing the access token back to the client
    if hasattr(tld, "new_access_token") and tld.new_access_token:
        response.set_cookie("access_token", tld.new_access_token, domain=domain_for_frontend_cookie)

    # id_token is required for logging out since this gets passed back to the openid server
    if hasattr(tld, "new_id_token") and tld.new_id_token:
        response.set_cookie("id_token", tld.new_id_token, domain=domain_for_frontend_cookie)

    if hasattr(tld, "user_has_logged_out") and tld.user_has_logged_out:
        response.set_cookie("id_token", "", max_age=0, domain=domain_for_frontend_cookie)
        response.set_cookie("access_token", "", max_age=0, domain=domain_for_frontend_cookie)

    _clear_auth_tokens_from_thread_local_data()

    return response


# we could parse the redirect url and see if it looks like a task show page url.
# we could also pass a query param from the frontend with the task guid and only
# look into guest access if the query param was present. then we look to see if the
# task is specified as guest access in the task spec (via an extension or something).
# if so, possibly we put something in a cookie to let us know, or maybe we don't need
# to do that because the token already has the correct restricted permisions?
def login(redirect_url: str = "/", process_instance_id: int | None = None, task_guid: str | None = None) -> Response:
    if current_app.config.get("SPIFFWORKFLOW_BACKEND_AUTHENTICATION_DISABLED"):
        AuthorizationService.create_anonymous_token(
            username=SPIFF_NO_AUTH_USER,
            group_identifier=SPIFF_NO_AUTH_USER,
            permission_target="/*",
        )
        return redirect(redirect_url)

    if process_instance_id and task_guid:
        # TODO: check task can be completed anonymously
        AuthorizationService.create_anonymous_token(
            username=SPIFF_ANONYMOUS_USER,
            group_identifier=SPIFF_ANONYMOUS_USER,
        )

    state = AuthenticationService.generate_state(redirect_url)
    login_redirect_url = AuthenticationService().get_login_redirect_url(state.decode("UTF-8"))
    return redirect(login_redirect_url)


def parse_id_token(token: str) -> Any:
    """Parse the id token."""
    parts = token.split(".")
    if len(parts) != 3:
        raise Exception("Incorrect id token format")

    payload = parts[1]
    padded = payload + "=" * (4 - len(payload) % 4)
    decoded = base64.b64decode(padded)
    return json.loads(decoded)


def login_return(code: str, state: str, session_state: str = "") -> Response | None:
    state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))
    state_redirect_url = state_dict["redirect_url"]
    auth_token_object = AuthenticationService().get_auth_token_object(code)
    if "id_token" in auth_token_object:
        id_token = auth_token_object["id_token"]
        user_info = parse_id_token(id_token)

        if AuthenticationService.validate_id_or_access_token(id_token):
            if user_info and "error" not in user_info:
                user_model = AuthorizationService.create_user_from_sign_in(user_info)
                g.user = user_model.id
                g.token = auth_token_object["id_token"]
                if "refresh_token" in auth_token_object:
                    AuthenticationService.store_refresh_token(user_model.id, auth_token_object["refresh_token"])
                redirect_url = state_redirect_url
                tld = current_app.config["THREAD_LOCAL_DATA"]
                tld.new_access_token = auth_token_object["id_token"]
                tld.new_id_token = auth_token_object["id_token"]
                return redirect(redirect_url)

        raise ApiError(
            error_code="invalid_login",
            message="Login failed. Please try again",
            status_code=401,
        )

    else:
        current_app.logger.error(f"id_token not found in payload from provider: {auth_token_object}")
        raise ApiError(
            error_code="invalid_token",
            message="Login failed. Please try again",
            status_code=401,
        )


# FIXME: share more code with login_return and maybe attempt to get a refresh token
def login_with_access_token(access_token: str) -> Response:
    user_info = parse_id_token(access_token)

    if AuthenticationService.validate_id_or_access_token(access_token):
        if user_info and "error" not in user_info:
            AuthorizationService.create_user_from_sign_in(user_info)
    else:
        raise ApiError(
            error_code="invalid_login",
            message="Login failed. Please try again",
            status_code=401,
        )

    return make_response(jsonify({"ok": True}))


def login_api() -> Response:
    redirect_url = "/v1.0/login_api_return"
    state = AuthenticationService.generate_state(redirect_url)
    login_redirect_url = AuthenticationService().get_login_redirect_url(state.decode("UTF-8"), redirect_url)
    return redirect(login_redirect_url)


def login_api_return(code: str, state: str, session_state: str) -> str:
    state_dict = ast.literal_eval(base64.b64decode(state).decode("utf-8"))
    state_dict["redirect_url"]

    auth_token_object = AuthenticationService().get_auth_token_object(code, "/v1.0/login_api_return")
    access_token: str = auth_token_object["access_token"]
    if access_token is None:
        raise MissingAccessTokenError("Cannot find the access token for the request")

    return access_token


def logout(id_token: str, redirect_url: str | None) -> Response:
    if redirect_url is None:
        redirect_url = ""
    tld = current_app.config["THREAD_LOCAL_DATA"]
    tld.user_has_logged_out = True
    return AuthenticationService().logout(redirect_url=redirect_url, id_token=id_token)


def logout_return() -> Response:
    frontend_url = str(current_app.config["SPIFFWORKFLOW_BACKEND_URL_FOR_FRONTEND"])
    return redirect(f"{frontend_url}/")


def get_decoded_token(token: str) -> dict | None:
    try:
        decoded_token = jwt.decode(token, options={"verify_signature": False})
    except Exception as e:
        raise ApiError(error_code="invalid_token", message="Cannot decode token.") from e
    else:
        if "token_type" in decoded_token or "iss" in decoded_token:
            return decoded_token
        else:
            current_app.logger.error(f"Unknown token type in get_decoded_token: token: {token}")
            raise ApiError(
                error_code="unknown_token",
                message="Unknown token type in get_decoded_token",
            )


def get_scope(token: str) -> str:
    scope = ""
    decoded_token = jwt.decode(token, options={"verify_signature": False})
    if "scope" in decoded_token:
        scope = decoded_token["scope"]
    return scope


def get_user_from_decoded_internal_token(decoded_token: dict) -> UserModel | None:
    sub = decoded_token["sub"]
    parts = sub.split("::")
    service = parts[0].split(":")[1]
    service_id = parts[1].split(":")[1]
    user: UserModel = (
        UserModel.query.filter(UserModel.service == service).filter(UserModel.service_id == service_id).first()
    )
    if user:
        return user
    user = UserService.create_user(service_id, service, service_id)
    return user


def _clear_auth_tokens_from_thread_local_data() -> None:
    tld = current_app.config["THREAD_LOCAL_DATA"]
    if hasattr(tld, "new_access_token"):
        delattr(tld, "new_access_token")
    if hasattr(tld, "new_id_token"):
        delattr(tld, "new_id_token")
    if hasattr(tld, "user_has_logged_out"):
        delattr(tld, "user_has_logged_out")

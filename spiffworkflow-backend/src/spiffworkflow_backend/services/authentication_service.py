"""Authentication_service."""
import base64
import enum
import json
import time
from typing import Optional

import jwt
import requests
from flask import current_app
from flask import redirect
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from werkzeug.wrappers import Response

from spiffworkflow_backend.models.refresh_token import RefreshTokenModel


class AuthenticationProviderTypes(enum.Enum):
    """AuthenticationServiceProviders."""

    open_id = "open_id"
    internal = "internal"


class AuthenticationService:
    """AuthenticationService."""

    @staticmethod
    def get_open_id_args() -> tuple:
        """Get_open_id_args."""
        open_id_server_url = current_app.config["OPEN_ID_SERVER_URL"]
        open_id_client_id = current_app.config["OPEN_ID_CLIENT_ID"]
        open_id_realm_name = current_app.config["OPEN_ID_REALM_NAME"]
        open_id_client_secret_key = current_app.config[
            "OPEN_ID_CLIENT_SECRET_KEY"
        ]  # noqa: S105
        return (
            open_id_server_url,
            open_id_client_id,
            open_id_realm_name,
            open_id_client_secret_key,
        )

    @staticmethod
    def get_backend_url() -> str:
        """Get_backend_url."""
        return str(current_app.config["SPIFFWORKFLOW_BACKEND_URL"])

    def logout(self, id_token: str, redirect_url: Optional[str] = None) -> Response:
        """Logout."""
        if redirect_url is None:
            redirect_url = "/"
        return_redirect_url = f"{self.get_backend_url()}/v1.0/logout_return"
        (
            open_id_server_url,
            open_id_client_id,
            open_id_realm_name,
            open_id_client_secret_key,
        ) = AuthenticationService.get_open_id_args()
        request_url = (
            f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/logout?"
            + f"post_logout_redirect_uri={return_redirect_url}&"
            + f"id_token_hint={id_token}"
        )

        return redirect(request_url)

    @staticmethod
    def generate_state(redirect_url: str) -> bytes:
        """Generate_state."""
        state = base64.b64encode(bytes(str({"redirect_url": redirect_url}), "UTF-8"))
        return state

    def get_login_redirect_url(
        self, state: str, redirect_url: str = "/v1.0/login_return"
    ) -> str:
        """Get_login_redirect_url."""
        (
            open_id_server_url,
            open_id_client_id,
            open_id_realm_name,
            open_id_client_secret_key,
        ) = AuthenticationService.get_open_id_args()
        return_redirect_url = f"{self.get_backend_url()}{redirect_url}"
        login_redirect_url = (
            f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/auth?"
            + f"state={state}&"
            + "response_type=code&"
            + f"client_id={open_id_client_id}&"
            + "scope=openid&"
            + f"redirect_uri={return_redirect_url}"
        )
        return login_redirect_url

    def get_auth_token_object(
        self, code: str, redirect_url: str = "/v1.0/login_return"
    ) -> dict:
        """Get_auth_token_object."""
        (
            open_id_server_url,
            open_id_client_id,
            open_id_realm_name,
            open_id_client_secret_key,
        ) = AuthenticationService.get_open_id_args()

        backend_basic_auth_string = f"{open_id_client_id}:{open_id_client_secret_key}"
        backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
        backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
        }
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": f"{self.get_backend_url()}{redirect_url}",
        }

        request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"

        response = requests.post(request_url, data=data, headers=headers)
        auth_token_object: dict = json.loads(response.text)
        return auth_token_object

    @classmethod
    def validate_id_token(cls, id_token: str) -> bool:
        """Https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation."""
        valid = True
        now = time.time()
        (
            open_id_server_url,
            open_id_client_id,
            open_id_realm_name,
            open_id_client_secret_key,
        ) = cls.get_open_id_args()
        try:
            decoded_token = jwt.decode(id_token, options={"verify_signature": False})
        except Exception as e:
            raise ApiError(
                error_code="bad_id_token",
                message="Cannot decode id_token",
                status_code=401,
            ) from e
        if decoded_token["iss"] != f"{open_id_server_url}/realms/{open_id_realm_name}":
            valid = False
        elif (
            open_id_client_id not in decoded_token["aud"]
            and "account" not in decoded_token["aud"]
        ):
            valid = False
        elif "azp" in decoded_token and decoded_token["azp"] not in (
            open_id_client_id,
            "account",
        ):
            valid = False
        elif now < decoded_token["iat"]:
            valid = False

        if not valid:
            current_app.logger.error(f"Invalid token in validate_id_token: {id_token}")
            return False

        if now > decoded_token["exp"]:
            raise ApiError(
                error_code="invalid_token",
                message="Your token is expired. Please Login",
                status_code=401,
            )

        return True

    @staticmethod
    def store_refresh_token(user_id: int, refresh_token: str) -> None:
        """Store_refresh_token."""
        refresh_token_model = RefreshTokenModel.query.filter(
            RefreshTokenModel.user_id == user_id
        ).first()
        if refresh_token_model:
            refresh_token_model.token = refresh_token
        else:
            refresh_token_model = RefreshTokenModel(
                user_id=user_id, token=refresh_token
            )
        db.session.add(refresh_token_model)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ApiError(
                error_code="store_refresh_token_error",
                message=f"We could not store the refresh token. Original error is {e}",
            ) from e

    @staticmethod
    def get_refresh_token(user_id: int) -> Optional[str]:
        """Get_refresh_token."""
        refresh_token_object: RefreshTokenModel = RefreshTokenModel.query.filter(
            RefreshTokenModel.user_id == user_id
        ).first()
        assert refresh_token_object  # noqa: S101
        return refresh_token_object.token

    @classmethod
    def get_auth_token_from_refresh_token(cls, refresh_token: str) -> dict:
        """Get a new auth_token from a refresh_token."""
        (
            open_id_server_url,
            open_id_client_id,
            open_id_realm_name,
            open_id_client_secret_key,
        ) = cls.get_open_id_args()

        backend_basic_auth_string = f"{open_id_client_id}:{open_id_client_secret_key}"
        backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
        backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": open_id_client_id,
            "client_secret": open_id_client_secret_key,
        }

        request_url = f"{open_id_server_url}/realms/{open_id_realm_name}/protocol/openid-connect/token"

        response = requests.post(request_url, data=data, headers=headers)
        auth_token_object: dict = json.loads(response.text)
        return auth_token_object

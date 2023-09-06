import base64
import enum
import json
import time

import jwt
import requests
from flask import current_app
from flask import redirect
from spiffworkflow_backend.config import HTTP_REQUEST_TIMEOUT_SECONDS
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.refresh_token import RefreshTokenModel
from werkzeug.wrappers import Response


class MissingAccessTokenError(Exception):
    pass


class NotAuthorizedError(Exception):
    pass


class RefreshTokenStorageError(Exception):
    pass


class UserNotLoggedInError(Exception):
    pass


# These could be either 'id' OR 'access' tokens and we can't always know which


class TokenExpiredError(Exception):
    pass


class TokenInvalidError(Exception):
    pass


class TokenNotProvidedError(Exception):
    pass


class OpenIdConnectionError(Exception):
    pass


class AuthenticationProviderTypes(enum.Enum):
    open_id = "open_id"
    internal = "internal"


class AuthenticationService:
    ENDPOINT_CACHE: dict = {}  # We only need to find the openid endpoints once, then we can cache them.

    @staticmethod
    def client_id() -> str:
        """Returns the client id from the config."""
        return current_app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID", "")

    @staticmethod
    def server_url() -> str:
        """Returns the server url from the config."""
        return current_app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL", "")

    @staticmethod
    def secret_key() -> str:
        """Returns the secret key from the config."""
        return current_app.config.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY", "")

    @classmethod
    def open_id_endpoint_for_name(cls, name: str) -> str:
        """All openid systems provide a mapping of static names to the full path of that endpoint."""
        openid_config_url = f"{cls.server_url()}/.well-known/openid-configuration"
        if name not in AuthenticationService.ENDPOINT_CACHE:
            try:
                response = requests.get(openid_config_url, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
                AuthenticationService.ENDPOINT_CACHE = response.json()
            except requests.exceptions.ConnectionError as ce:
                raise OpenIdConnectionError(f"Cannot connect to given open id url: {openid_config_url}") from ce
        if name not in AuthenticationService.ENDPOINT_CACHE:
            raise Exception(f"Unknown OpenID Endpoint: {name}. Tried to get from {openid_config_url}")
        return AuthenticationService.ENDPOINT_CACHE.get(name, "")

    @staticmethod
    def get_backend_url() -> str:
        return str(current_app.config["SPIFFWORKFLOW_BACKEND_URL"])

    def logout(self, id_token: str, redirect_url: str | None = None) -> Response:
        if redirect_url is None:
            redirect_url = f"{self.get_backend_url()}/v1.0/logout_return"
        request_url = (
            self.open_id_endpoint_for_name("end_session_endpoint")
            + f"?post_logout_redirect_uri={redirect_url}&"
            + f"id_token_hint={id_token}"
        )

        return redirect(request_url)

    @staticmethod
    def generate_state(redirect_url: str) -> bytes:
        state = base64.b64encode(bytes(str({"redirect_url": redirect_url}), "UTF-8"))
        return state

    def get_login_redirect_url(self, state: str, redirect_url: str = "/v1.0/login_return") -> str:
        return_redirect_url = f"{self.get_backend_url()}{redirect_url}"
        login_redirect_url = (
            self.open_id_endpoint_for_name("authorization_endpoint")
            + f"?state={state}&"
            + "response_type=code&"
            + f"client_id={self.client_id()}&"
            + "scope=openid profile email&"
            + f"redirect_uri={return_redirect_url}"
        )
        return login_redirect_url

    def get_auth_token_object(self, code: str, redirect_url: str = "/v1.0/login_return") -> dict:
        backend_basic_auth_string = f"{self.client_id()}:{self.secret_key()}"
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

        request_url = self.open_id_endpoint_for_name("token_endpoint")

        response = requests.post(request_url, data=data, headers=headers, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
        auth_token_object: dict = json.loads(response.text)
        return auth_token_object

    @classmethod
    def validate_id_or_access_token(cls, token: str) -> bool:
        """Https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation."""
        valid = True
        now = round(time.time())
        try:
            decoded_token = jwt.decode(token, options={"verify_signature": False})
        except Exception as e:
            raise TokenInvalidError("Cannot decode token") from e

        # give a 5 second leeway to iat in case keycloak server time doesn't match backend server
        iat_clock_skew_leeway = 5

        iss = decoded_token["iss"]
        aud = decoded_token["aud"]
        azp = decoded_token["azp"] if "azp" in decoded_token else None
        iat = decoded_token["iat"]

        valid_audience_values = (cls.client_id(), "account")
        audience_array_in_token = aud
        if isinstance(aud, str):
            audience_array_in_token = [aud]
        overlapping_aud_values = [x for x in audience_array_in_token if x in valid_audience_values]

        if iss != cls.server_url():
            current_app.logger.error(
                f"TOKEN INVALID because ISS '{iss}' does not match server url '{cls.server_url()}'"
            )
            valid = False
        # aud could be an array or a string
        elif len(overlapping_aud_values) < 1:
            current_app.logger.error(
                f"TOKEN INVALID because audience '{aud}' does not match client id '{cls.client_id()}'"
            )
            valid = False
        elif azp and azp not in (
            cls.client_id(),
            "account",
        ):
            current_app.logger.error(f"TOKEN INVALID because azp '{azp}' does not match client id '{cls.client_id()}'")
            valid = False
        # make sure issued at time is not in the future
        elif now + iat_clock_skew_leeway < iat:
            current_app.logger.error(
                f"TOKEN INVALID because iat '{iat}' is in the future relative to server now '{now}'"
            )
            valid = False

        if valid and now > decoded_token["exp"]:
            raise TokenExpiredError("Your token is expired. Please Login")
        elif not valid:
            current_app.logger.error(
                "TOKEN INVALID: details: "
                f"ISS: {iss} "
                f"AUD: {aud} "
                f"AZP: {azp} "
                f"IAT: {iat} "
                f"SERVER_URL: {cls.server_url()} "
                f"CLIENT_ID: {cls.client_id()} "
                f"NOW: {now}"
            )

        return valid

    @staticmethod
    def store_refresh_token(user_id: int, refresh_token: str) -> None:
        refresh_token_model = RefreshTokenModel.query.filter(RefreshTokenModel.user_id == user_id).first()
        if refresh_token_model:
            refresh_token_model.token = refresh_token
        else:
            refresh_token_model = RefreshTokenModel(user_id=user_id, token=refresh_token)
        db.session.add(refresh_token_model)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise RefreshTokenStorageError(
                f"We could not store the refresh token. Original error is {e}",
            ) from e

    @staticmethod
    def get_refresh_token(user_id: int) -> str | None:
        refresh_token_object: RefreshTokenModel = RefreshTokenModel.query.filter(
            RefreshTokenModel.user_id == user_id
        ).first()
        if refresh_token_object:
            return refresh_token_object.token
        return None

    @classmethod
    def get_auth_token_from_refresh_token(cls, refresh_token: str) -> dict:
        """Converts a refresh token to an Auth Token by calling the openid's auth endpoint."""
        backend_basic_auth_string = f"{cls.client_id()}:{cls.secret_key()}"
        backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
        backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cls.client_id(),
            "client_secret": cls.secret_key(),
        }

        request_url = cls.open_id_endpoint_for_name("token_endpoint")

        response = requests.post(request_url, data=data, headers=headers, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
        auth_token_object: dict = json.loads(response.text)
        return auth_token_object

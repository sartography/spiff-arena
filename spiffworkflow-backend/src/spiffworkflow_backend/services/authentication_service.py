import base64
import enum
import json
import time
from hashlib import sha256
from hmac import HMAC
from hmac import compare_digest
from typing import TypedDict

import jwt
import requests
from flask import current_app
from flask import g
from flask import redirect
from flask import request
from werkzeug.wrappers import Response

from spiffworkflow_backend.config import HTTP_REQUEST_TIMEOUT_SECONDS
from spiffworkflow_backend.exceptions.error import OpenIdConnectionError
from spiffworkflow_backend.exceptions.error import RefreshTokenStorageError
from spiffworkflow_backend.exceptions.error import TokenExpiredError
from spiffworkflow_backend.exceptions.error import TokenInvalidError
from spiffworkflow_backend.exceptions.error import TokenNotProvidedError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.refresh_token import RefreshTokenModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.user_service import UserService


class AuthenticationProviderTypes(enum.Enum):
    open_id = "open_id"
    internal = "internal"


class AuthenticationOptionForApi(TypedDict):
    identifier: str
    label: str
    uri: str


class AuthenticationOption(AuthenticationOptionForApi):
    client_id: str
    client_secret: str


class AuthenticationOptionNotFoundError(Exception):
    pass


class AuthenticationService:
    ENDPOINT_CACHE: dict[str, dict[str, str]] = (
        {}
    )  # We only need to find the openid endpoints once, then we can cache them.

    @classmethod
    def authentication_options_for_api(cls) -> list[AuthenticationOptionForApi]:
        # ensure we remove sensitive info such as client secret from the config before sending it back
        configs: list[AuthenticationOptionForApi] = []
        for config in current_app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"]:
            configs.append(
                {
                    "identifier": config["identifier"],
                    "label": config["label"],
                    "uri": config["uri"],
                }
            )
        return configs

    @classmethod
    def authentication_option_for_identifier(cls, authentication_identifier: str) -> AuthenticationOption:
        for config in current_app.config["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"]:
            if config["identifier"] == authentication_identifier:
                return_config: AuthenticationOption = config
                return return_config
        raise AuthenticationOptionNotFoundError(
            f"Could not find a config with identifier '{authentication_identifier}'"
        )

    @classmethod
    def client_id(cls, authentication_identifier: str) -> str:
        """Returns the client id from the config."""
        config: str = cls.authentication_option_for_identifier(authentication_identifier)["client_id"]
        return config

    @classmethod
    def server_url(cls, authentication_identifier: str) -> str:
        """Returns the server url from the config."""
        config: str = cls.authentication_option_for_identifier(authentication_identifier)["uri"]
        return config

    @classmethod
    def secret_key(cls, authentication_identifier: str) -> str:
        """Returns the secret key from the config."""
        config: str = cls.authentication_option_for_identifier(authentication_identifier)["client_secret"]
        return config

    @classmethod
    def open_id_endpoint_for_name(cls, name: str, authentication_identifier: str) -> str:
        """All openid systems provide a mapping of static names to the full path of that endpoint."""
        openid_config_url = f"{cls.server_url(authentication_identifier)}/.well-known/openid-configuration"
        if authentication_identifier not in cls.ENDPOINT_CACHE:
            cls.ENDPOINT_CACHE[authentication_identifier] = {}
        if name not in AuthenticationService.ENDPOINT_CACHE[authentication_identifier]:
            try:
                response = requests.get(openid_config_url, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
                AuthenticationService.ENDPOINT_CACHE[authentication_identifier] = response.json()
            except requests.exceptions.ConnectionError as ce:
                raise OpenIdConnectionError(f"Cannot connect to given open id url: {openid_config_url}") from ce
        if name not in AuthenticationService.ENDPOINT_CACHE[authentication_identifier]:
            raise Exception(f"Unknown OpenID Endpoint: {name}. Tried to get from {openid_config_url}")
        config: str = AuthenticationService.ENDPOINT_CACHE[authentication_identifier].get(name, "")
        return config

    @staticmethod
    def get_backend_url() -> str:
        return str(current_app.config["SPIFFWORKFLOW_BACKEND_URL"])

    def logout(self, id_token: str, authentication_identifier: str, redirect_url: str | None = None) -> Response:
        if redirect_url is None:
            redirect_url = f"{self.get_backend_url()}/v1.0/logout_return"
        request_url = (
            self.open_id_endpoint_for_name("end_session_endpoint", authentication_identifier=authentication_identifier)
            + f"?post_logout_redirect_uri={redirect_url}&"
            + f"id_token_hint={id_token}"
        )

        return redirect(request_url)

    @staticmethod
    def generate_state(redirect_url: str, authentication_identifier: str) -> bytes:
        state = base64.b64encode(
            bytes(str({"redirect_url": redirect_url, "authentication_identifier": authentication_identifier}), "UTF-8")
        )
        return state

    def get_login_redirect_url(
        self, state: str, authentication_identifier: str, redirect_url: str = "/v1.0/login_return"
    ) -> str:
        return_redirect_url = f"{self.get_backend_url()}{redirect_url}"
        login_redirect_url = (
            self.open_id_endpoint_for_name(
                "authorization_endpoint", authentication_identifier=authentication_identifier
            )
            + f"?state={state}&"
            + "response_type=code&"
            + f"client_id={self.client_id(authentication_identifier)}&"
            + "scope=openid profile email&"
            + f"redirect_uri={return_redirect_url}"
        )
        return login_redirect_url

    def get_auth_token_object(
        self, code: str, authentication_identifier: str, redirect_url: str = "/v1.0/login_return"
    ) -> dict:
        backend_basic_auth_string = (
            f"{self.client_id(authentication_identifier)}:{self.__class__.secret_key(authentication_identifier)}"
        )
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

        request_url = self.open_id_endpoint_for_name(
            "token_endpoint", authentication_identifier=authentication_identifier
        )

        response = requests.post(request_url, data=data, headers=headers, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
        auth_token_object: dict = json.loads(response.text)
        return auth_token_object

    @classmethod
    def validate_id_or_access_token(cls, token: str, authentication_identifier: str) -> bool:
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

        valid_audience_values = (cls.client_id(authentication_identifier), "account")
        audience_array_in_token = aud
        if isinstance(aud, str):
            audience_array_in_token = [aud]
        overlapping_aud_values = [x for x in audience_array_in_token if x in valid_audience_values]

        if iss != cls.server_url(authentication_identifier):
            current_app.logger.error(
                f"TOKEN INVALID because ISS '{iss}' does not match server url"
                f" '{cls.server_url(authentication_identifier)}'"
            )
            valid = False
        # aud could be an array or a string
        elif len(overlapping_aud_values) < 1:
            current_app.logger.error(
                f"TOKEN INVALID because audience '{aud}' does not match client id"
                f" '{cls.client_id(authentication_identifier)}'"
            )
            valid = False
        elif azp and azp not in (
            cls.client_id(authentication_identifier),
            "account",
        ):
            current_app.logger.error(
                f"TOKEN INVALID because azp '{azp}' does not match client id"
                f" '{cls.client_id(authentication_identifier)}'"
            )
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
                f"SERVER_URL: {cls.server_url(authentication_identifier)} "
                f"CLIENT_ID: {cls.client_id(authentication_identifier)} "
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
    def get_auth_token_from_refresh_token(cls, refresh_token: str, authentication_identifier: str) -> dict:
        """Converts a refresh token to an Auth Token by calling the openid's auth endpoint."""
        backend_basic_auth_string = (
            f"{cls.client_id(authentication_identifier)}:{cls.secret_key(authentication_identifier)}"
        )
        backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
        backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
        }

        data = {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": cls.client_id(authentication_identifier),
            "client_secret": cls.secret_key(authentication_identifier),
        }

        request_url = cls.open_id_endpoint_for_name(
            "token_endpoint", authentication_identifier=authentication_identifier
        )

        response = requests.post(request_url, data=data, headers=headers, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
        auth_token_object: dict = json.loads(response.text)
        return auth_token_object

    @staticmethod
    def decode_auth_token(auth_token: str) -> dict[str, str | None]:
        """This is only used for debugging."""
        try:
            payload: dict[str, str | None] = jwt.decode(auth_token, options={"verify_signature": False})
            return payload
        except jwt.ExpiredSignatureError as exception:
            raise TokenExpiredError(
                "The Authentication token you provided expired and must be renewed.",
            ) from exception
        except jwt.InvalidTokenError as exception:
            raise TokenInvalidError(
                "The Authentication token you provided is invalid. You need a new token. ",
            ) from exception

    # https://stackoverflow.com/a/71320673/6090676
    @classmethod
    def verify_sha256_token(cls, auth_header: str | None) -> None:
        if auth_header is None:
            raise TokenNotProvidedError(
                "unauthorized",
            )

        received_sign = auth_header.split("sha256=")[-1].strip()
        secret = current_app.config["SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET"].encode()
        expected_sign = HMAC(key=secret, msg=request.data, digestmod=sha256).hexdigest()
        if not compare_digest(received_sign, expected_sign):
            raise TokenInvalidError(
                "unauthorized",
            )

    @classmethod
    def create_guest_token(
        cls,
        username: str,
        group_identifier: str,
        authentication_identifier: str,
        permission_target: str | None = None,
        permission: str = "all",
        auth_token_properties: dict | None = None,
    ) -> None:
        guest_user = UserService.find_or_create_guest_user(username=username, group_identifier=group_identifier)
        if permission_target is not None:
            AuthorizationService.add_permission_from_uri_or_macro(
                group_identifier, permission=permission, target=permission_target
            )
        g.user = guest_user
        g.token = guest_user.encode_auth_token(auth_token_properties)
        tld = current_app.config["THREAD_LOCAL_DATA"]
        tld.new_access_token = g.token
        tld.new_id_token = g.token
        tld.new_authentication_identifier = authentication_identifier

    @classmethod
    def set_user_has_logged_out(cls) -> None:
        tld = current_app.config["THREAD_LOCAL_DATA"]
        tld.user_has_logged_out = True

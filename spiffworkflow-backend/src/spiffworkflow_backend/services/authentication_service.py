import base64
import enum
import json
import sys
import time
from hashlib import sha256
from hmac import HMAC
from hmac import compare_digest
from typing import Any
from typing import cast

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509 import load_der_x509_certificate
from flask import url_for
from security import safe_requests  # type: ignore

from spiffworkflow_backend.models.user import SPIFF_GENERATED_JWT_ALGORITHM
from spiffworkflow_backend.models.user import SPIFF_GENERATED_JWT_AUDIENCE
from spiffworkflow_backend.models.user import SPIFF_GENERATED_JWT_KEY_ID
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.openid_blueprint.openid_blueprint import SPIFF_OPEN_ID_KEY_ID

if sys.version_info < (3, 11):
    from typing_extensions import NotRequired
    from typing_extensions import TypedDict
else:
    from typing import NotRequired
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


class JWKSKeyConfig(TypedDict):
    kid: str
    kty: str
    use: str
    n: str
    e: str
    x5c: NotRequired[list[str]]
    alg: str
    x5t: str


class JWKSConfigs(TypedDict):
    keys: NotRequired[list[JWKSKeyConfig]]


class AuthenticationProviderTypes(enum.Enum):
    open_id = "open_id"
    internal = "internal"


class AuthenticationOptionForApi(TypedDict):
    identifier: str
    label: str
    internal_uri: NotRequired[str]
    uri: str
    additional_valid_client_ids: NotRequired[str]


class AuthenticationOption(AuthenticationOptionForApi):
    client_id: str
    client_secret: str


class AuthenticationOptionNotFoundError(Exception):
    pass


class AuthenticationService:
    ENDPOINT_CACHE: dict[str, dict[str, str]] = {}  # We only need to find the openid endpoints once, then we can cache them.
    JSON_WEB_KEYSET_CACHE: dict[str, JWKSConfigs] = {}

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
        raise AuthenticationOptionNotFoundError(f"Could not find a config with identifier '{authentication_identifier}'")

    @classmethod
    def client_id(cls, authentication_identifier: str) -> str:
        """Returns the client id from the config."""
        config: str = cls.authentication_option_for_identifier(authentication_identifier)["client_id"]
        return config

    @classmethod
    def valid_audiences(cls, authentication_identifier: str) -> list[str]:
        return [cls.client_id(authentication_identifier), "account"]

    @classmethod
    def server_url(cls, authentication_identifier: str, internal: bool = False) -> str:
        """Returns the server url from the config."""
        auth_config = cls.authentication_option_for_identifier(authentication_identifier)
        uri_key = "uri"
        if internal:
            if "internal_uri" in auth_config and auth_config["internal_uri"] is not None:
                uri_key = "internal_uri"
        config: str = auth_config[uri_key]  # type: ignore
        return config

    @classmethod
    def secret_key(cls, authentication_identifier: str) -> str:
        """Returns the secret key from the config."""
        config: str = cls.authentication_option_for_identifier(authentication_identifier)["client_secret"]
        return config

    @classmethod
    def open_id_endpoint_for_name(cls, name: str, authentication_identifier: str, internal: bool = False) -> str:
        """All openid systems provide a mapping of static names to the full path of that endpoint."""

        if authentication_identifier not in cls.ENDPOINT_CACHE:
            cls.ENDPOINT_CACHE[authentication_identifier] = {}
        if authentication_identifier not in cls.JSON_WEB_KEYSET_CACHE:
            cls.JSON_WEB_KEYSET_CACHE[authentication_identifier] = {}

        internal_server_url = cls.server_url(authentication_identifier, internal=True)
        openid_config_url = f"{internal_server_url}/.well-known/openid-configuration"
        if name not in AuthenticationService.ENDPOINT_CACHE[authentication_identifier]:
            try:
                response = safe_requests.get(openid_config_url, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
                AuthenticationService.ENDPOINT_CACHE[authentication_identifier] = response.json()
            except requests.exceptions.ConnectionError as ce:
                raise OpenIdConnectionError(f"Cannot connect to given open id url: {openid_config_url}") from ce
        if name not in AuthenticationService.ENDPOINT_CACHE[authentication_identifier]:
            raise Exception(f"Unknown OpenID Endpoint: {name}. Tried to get from {openid_config_url}")

        config: str = AuthenticationService.ENDPOINT_CACHE[authentication_identifier].get(name, "")

        external_server_url = cls.server_url(authentication_identifier)
        if internal is False:
            if internal_server_url != external_server_url:
                config = config.replace(internal_server_url, external_server_url)

        return config

    @classmethod
    def get_jwks_config_from_uri(cls, jwks_uri: str, force_refresh: bool = False) -> JWKSConfigs:
        if jwks_uri not in cls.JSON_WEB_KEYSET_CACHE or force_refresh:
            try:
                jwt_ks_response = safe_requests.get(jwks_uri, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
                cls.JSON_WEB_KEYSET_CACHE[jwks_uri] = jwt_ks_response.json()
            except requests.exceptions.ConnectionError as ce:
                raise OpenIdConnectionError(f"Cannot connect to given jwks url: {jwks_uri}") from ce
        return AuthenticationService.JSON_WEB_KEYSET_CACHE[jwks_uri]

    @classmethod
    def jwks_public_key_for_key_id(cls, authentication_identifier: str, key_id: str) -> JWKSKeyConfig:
        jwks_uri = cls.open_id_endpoint_for_name("jwks_uri", authentication_identifier, internal=True)
        jwks_configs = cls.get_jwks_config_from_uri(jwks_uri)
        json_key_configs: JWKSKeyConfig | None = cls.get_key_config(jwks_configs, key_id)
        if not json_key_configs:
            # Refetch the JWKS keys from the source if key_id is not found in cache
            jwks_configs = cls.get_jwks_config_from_uri(jwks_uri, force_refresh=True)
            json_key_configs = cls.get_key_config(jwks_configs, key_id)
            if not json_key_configs:
                raise KeyError(f"Key ID {key_id} not found in JWKS even after refreshing from {jwks_uri}.")
        return json_key_configs

    @classmethod
    def public_key_from_rsa_public_numbers(cls, json_key_configs: JWKSKeyConfig) -> Any:
        modulus = base64.urlsafe_b64decode(json_key_configs["n"] + "===")
        exponent = base64.urlsafe_b64decode(json_key_configs["e"] + "===")
        public_key_numbers = rsa.RSAPublicNumbers(
            int.from_bytes(exponent, byteorder="big"), int.from_bytes(modulus, byteorder="big")
        )
        return public_key_numbers.public_key(backend=default_backend())

    @classmethod
    def public_key_from_x5c(cls, key_id: str, json_key_configs: JWKSKeyConfig) -> Any:
        x5c = json_key_configs["x5c"][0]
        decoded_certificate = base64.b64decode(x5c)

        # our backend-based openid provider implementation (which you should never use in prod)
        # uses a public/private key pair. we played around with adding an x509 cert so we could
        # follow the exact same mechanism for getting the public key that we use for keycloak,
        # but using an x509 cert for no reason seemed a little overboard for this toy-openid use case,
        # when we already have the public key that can work hardcoded in our config.
        if key_id == SPIFF_OPEN_ID_KEY_ID:
            return decoded_certificate
        else:
            x509_cert = load_der_x509_certificate(decoded_certificate, default_backend())
            return x509_cert.public_key()

    @classmethod
    def parse_jwt_token(cls, authentication_identifier: str, token: str) -> dict:
        header = jwt.get_unverified_header(token)
        key_id = str(header.get("kid"))
        parsed_token: dict | None = None

        # if the token has our key id then we issued it and should verify to ensure it's valid
        if key_id == SPIFF_GENERATED_JWT_KEY_ID:
            parsed_token = jwt.decode(
                token,
                str(current_app.secret_key),
                algorithms=[SPIFF_GENERATED_JWT_ALGORITHM],
                audience=SPIFF_GENERATED_JWT_AUDIENCE,
                options={"verify_exp": False},
            )
        else:
            algorithm = str(header.get("alg"))
            json_key_configs = cls.jwks_public_key_for_key_id(authentication_identifier, key_id)
            public_key: Any = None
            jwt_decode_options = {
                "verify_exp": False,
                "verify_aud": False,
                "verify_iat": current_app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_IAT"],
                "verify_nbf": current_app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_VERIFY_NBF"],
                "leeway": current_app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_LEEWAY"],
            }

            if "x5c" not in json_key_configs:
                public_key = cls.public_key_from_rsa_public_numbers(json_key_configs)
            else:
                public_key = cls.public_key_from_x5c(key_id, json_key_configs)

            # tokens generated from the cli have an aud like: [ "realm-management", "account" ]
            # while tokens generated from frontend have an aud like: "spiffworkflow-backend."
            # as such, we cannot simply pull the first valid audience out of cls.valid_audiences(authentication_identifier)
            # and then shove it into decode (it will raise), but we need the algorithm from validate_decoded_token that checks
            # if the audience in the token matches any of the valid audience values. Therefore do not check aud here.
            parsed_token = jwt.decode(
                token,
                public_key,
                algorithms=[algorithm],
                audience=cls.valid_audiences(authentication_identifier)[0],
                options=jwt_decode_options,
            )
        return cast(dict, parsed_token)

    # returns either https://spiffworkflow.example.com or https://spiffworkflow.example.com/api
    @staticmethod
    def get_backend_url() -> str:
        return str(current_app.config["SPIFFWORKFLOW_BACKEND_URL"])

    def logout(self, id_token: str, authentication_identifier: str, redirect_url: str | None = None) -> Response:
        if redirect_url is None:
            redirect_url = f"{self.get_backend_url()}/v1.0/logout_return"
        request_url = (
            self.__class__.open_id_endpoint_for_name("end_session_endpoint", authentication_identifier=authentication_identifier)
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

    def get_login_redirect_url(self, state: str, authentication_identifier: str, redirect_url: str | None = None) -> str:
        redirect_url_to_use = redirect_url
        if redirect_url_to_use is None:
            host_url = request.host_url.strip("/")
            login_return_path = url_for("/v1_0.spiffworkflow_backend_routes_authentication_controller_login_return")
            redirect_url_to_use = f"{host_url}{login_return_path}"
        login_redirect_url = (
            self.open_id_endpoint_for_name("authorization_endpoint", authentication_identifier=authentication_identifier)
            + f"?state={state}&"
            + "response_type=code&"
            + f"client_id={self.client_id(authentication_identifier)}&"
            + f"scope={current_app.config['SPIFFWORKFLOW_BACKEND_OPENID_SCOPE']}&"
            + f"redirect_uri={redirect_url_to_use}"
        )
        return login_redirect_url

    def get_auth_token_object(self, code: str, authentication_identifier: str, redirect_url: str = "/v1.0/login_return") -> dict:
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
            "token_endpoint", authentication_identifier=authentication_identifier, internal=True
        )

        response = requests.post(request_url, data=data, headers=headers, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
        auth_token_object: dict = json.loads(response.text)
        return auth_token_object

    @classmethod
    def is_valid_azp(cls, authentication_identifier: str, azp: str | None) -> bool:
        # not all open id token include an azp so only check if present
        if azp is None:
            return True

        valid_client_ids = [cls.client_id(authentication_identifier)]
        if (
            "additional_valid_client_ids" in cls.authentication_option_for_identifier(authentication_identifier)
            and cls.authentication_option_for_identifier(authentication_identifier)["additional_valid_client_ids"] is not None
        ):
            additional_valid_client_ids = cls.authentication_option_for_identifier(authentication_identifier)[
                "additional_valid_client_ids"
            ].split(",")
            additional_valid_client_ids = [value.strip() for value in additional_valid_client_ids]
            valid_client_ids = valid_client_ids + additional_valid_client_ids
        return azp in valid_client_ids

    @classmethod
    def validate_decoded_token(cls, decoded_token: dict, authentication_identifier: str) -> bool:
        """Https://openid.net/specs/openid-connect-core-1_0.html#IDTokenValidation."""
        valid = True
        now = round(time.time())

        # TODO: use verify_exp True in jwt decode to check this instead
        iat_clock_skew_leeway = current_app.config["SPIFFWORKFLOW_BACKEND_OPEN_ID_LEEWAY"]

        iss = decoded_token["iss"]
        aud = decoded_token["aud"] if "aud" in decoded_token else None
        azp = decoded_token["azp"] if "azp" in decoded_token else None
        iat = decoded_token["iat"]

        valid_audience_values = cls.valid_audiences(authentication_identifier)
        audience_array_in_token = aud
        if isinstance(aud, str):
            audience_array_in_token = [aud]
        overlapping_aud_values = [x for x in audience_array_in_token if x in valid_audience_values]

        if iss not in [cls.server_url(authentication_identifier), UserModel.spiff_generated_jwt_issuer()]:
            current_app.logger.error(
                f"TOKEN INVALID because ISS '{iss}' does not match server url '{cls.server_url(authentication_identifier)}'"
            )
            valid = False
        # aud could be an array or a string
        elif len(overlapping_aud_values) < 1:
            current_app.logger.error(
                f"TOKEN INVALID because audience '{aud}' does not match client id '{cls.client_id(authentication_identifier)}'"
            )
            valid = False
        elif not cls.is_valid_azp(authentication_identifier, azp):
            current_app.logger.error(
                f"TOKEN INVALID because azp '{azp}' does not match client id '{cls.client_id(authentication_identifier)}'"
            )
            valid = False
        # make sure issued at time is not in the future
        elif now + iat_clock_skew_leeway < iat:
            current_app.logger.error(f"TOKEN INVALID because iat '{iat}' is in the future relative to server now '{now}'")
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
        refresh_token_object: RefreshTokenModel = RefreshTokenModel.query.filter(RefreshTokenModel.user_id == user_id).first()
        if refresh_token_object:
            return refresh_token_object.token
        return None

    @classmethod
    def get_key_config(cls, jwks_configs: JWKSConfigs, key_id: str) -> JWKSKeyConfig | None:
        for jk in jwks_configs["keys"]:
            if jk["kid"] == key_id:
                return jk
        return None

    @classmethod
    def get_auth_token_from_refresh_token(cls, refresh_token: str, authentication_identifier: str) -> dict:
        """Converts a refresh token to an Auth Token by calling the openid's auth endpoint."""
        backend_basic_auth_string = f"{cls.client_id(authentication_identifier)}:{cls.secret_key(authentication_identifier)}"
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
            "token_endpoint", authentication_identifier=authentication_identifier, internal=True
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

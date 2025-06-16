"""OpenID Implementation for demos and local development.

A very insecure and partial OpenID implementation for use in demos and testing.
Provides the bare minimum endpoints required by SpiffWorkflow to
handle openid authentication -- definitely not a production ready system.
This is just here to make local development, testing, and demonstration easier.
"""

import base64
import json
import math
import time
from typing import Any
from urllib.parse import urlencode

import jwt
import yaml
from flask import Blueprint
from flask import current_app
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from werkzeug.wrappers import Response

from spiffworkflow_backend.config.openid.rsa_keys import OpenIdConfigsForDevOnly

openid_blueprint = Blueprint("openid", __name__, template_folder="templates", static_folder="static")

OPEN_ID_CODE = ":this_is_not_secure_do_not_use_in_production"
SPIFF_OPEN_ID_KEY_ID = "spiffworkflow_backend_open_id"
SPIFF_OPEN_ID_ALGORITHM = "RS256"


# just so /openid responds so we can route to it with url_for for populating issuer
@openid_blueprint.route("", methods=["GET"])
def index() -> Response:
    return make_response({"ok": True}, 200)


@openid_blueprint.route("/.well-known/openid-configuration", methods=["GET"])
def well_known() -> dict:
    """Open ID Discovery endpoint.

    These urls can be very different from one openid impl to the next, this is just a small subset.
    """

    # using or instead of setting a default so we can set the env var to None in tests and this will still work
    host_url = _host_url_without_root_path()
    return {
        "issuer": f"{host_url}{url_for('openid.index')}",
        "authorization_endpoint": f"{host_url}{url_for('openid.auth')}",
        "token_endpoint": f"{host_url}{url_for('openid.token')}",
        "end_session_endpoint": f"{host_url}{url_for('openid.end_session')}",
        "jwks_uri": f"{host_url}{url_for('openid.jwks')}",
    }


@openid_blueprint.route("/auth", methods=["GET"])
def auth() -> str:
    """Accepts a series of parameters."""
    host_url = _host_url_without_root_path()
    return render_template(
        "login.html",
        state=request.args.get("state"),
        response_type=request.args.get("response_type"),
        client_id=request.args.get("client_id"),
        scope=request.args.get("scope"),
        redirect_uri=request.args.get("redirect_uri"),
        error_message=request.args.get("error_message", ""),
        host_url=host_url,
    )


@openid_blueprint.route("/form_submit", methods=["POST"])
def form_submit() -> Any:
    """Handles the login form submission."""
    users = get_users()
    if request.values["Uname"] in users and request.values["Pass"] == users[request.values["Uname"]]["password"]:
        # Redirect back to the end user with some detailed information
        state = request.values.get("state")
        data = {
            "state": state,
            "code": request.values["Uname"] + OPEN_ID_CODE,
            "session_state": "",
        }
        url = request.values.get("redirect_uri") + "?" + urlencode(data)
        return redirect(url)
    else:
        host_url = _host_url_without_root_path()
        return render_template(
            "login.html",
            state=request.values.get("state"),
            response_type=request.values.get("response_type"),
            client_id=request.values.get("client_id"),
            scope=request.values.get("scope"),
            redirect_uri=request.values.get("redirect_uri"),
            error_message="Login failed.  Please try again.",
            host_url=host_url,
        )


@openid_blueprint.route("/token", methods=["POST"])
def token() -> Response | dict:
    """Url that will return a valid token, given the super secret sauce."""
    code = request.values.get("code")

    if code is None:
        return Response(json.dumps({"error": "missing_code_value_in_token_request"}), status=400, mimetype="application/json")

    """We just stuffed the user name on the front of the code, so grab it."""
    user_name, secret_hash = code.split(":")
    user_details = get_users()[user_name]

    """Get authentication from headers."""
    authorization = request.headers.get("Authorization", "Basic ")
    authorization = authorization[6:]  # Remove "Basic"
    authorization = base64.b64decode(authorization).decode("utf-8")
    client_id = authorization.split(":")

    host_url = _host_url_without_root_path()
    private_key = OpenIdConfigsForDevOnly.private_key

    # this is just for testing. there is no need to expire tokens rapidly.
    one_hour = 3600
    one_day = one_hour * 24
    two_days = one_day * 2

    id_token = jwt.encode(
        {
            "iss": f"{host_url}{url_for('openid.index')}",
            "aud": client_id,
            "iat": math.floor(time.time()),
            "exp": round(time.time()) + two_days,
            "sub": user_name,
            "email": user_details["email"],
            "preferred_username": user_details.get("preferred_username", user_name),
        },
        private_key,
        algorithm=SPIFF_OPEN_ID_ALGORITHM,
        headers={"kid": SPIFF_OPEN_ID_KEY_ID},
    )
    response = {
        "access_token": id_token,
        "id_token": id_token,
        "refresh_token": id_token,
    }
    return response


@openid_blueprint.route("/end_session", methods=["GET"])
def end_session() -> Response:
    redirect_url = request.args.get("post_logout_redirect_uri", "http://localhost")
    request.args.get("id_token_hint")
    return redirect(redirect_url)


@openid_blueprint.route("/jwks", methods=["GET"])
def jwks() -> Response:
    public_key = base64.b64encode(OpenIdConfigsForDevOnly.public_key.encode()).decode("utf-8")
    jwks_configs = {
        "keys": [
            {
                "kid": SPIFF_OPEN_ID_KEY_ID,
                "kty": "RSA",
                "x5c": [public_key],
            }
        ]
    }
    return make_response(jsonify(jwks_configs), 200)


@openid_blueprint.route("/refresh", methods=["POST"])
def refresh() -> str:
    return ""


permission_cache = None


def get_users() -> Any:
    """Load users from a local configuration file."""
    global permission_cache  # noqa: PLW0603, allow global for performance
    if not permission_cache:
        with open(current_app.config["SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_ABSOLUTE_PATH"]) as file:
            permission_cache = yaml.safe_load(file)
    if "users" in permission_cache:
        return permission_cache["users"]
    else:
        return {}


# if backend is being hosted at http://localhost:7000/api because SPIFFWORKFLOW_BACKEND_WSGI_PATH_PREFIX=/api,
# this will return http://localhost:7000, because url_for will add the /api for us.
def _host_url_without_root_path() -> str:
    return request.host_url.strip("/")

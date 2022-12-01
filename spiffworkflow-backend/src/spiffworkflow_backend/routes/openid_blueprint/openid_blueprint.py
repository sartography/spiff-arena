"""
Provides the bare minimum endpoints required by SpiffWorkflow to
handle openid authentication -- definitely not a production ready system.
This is just here to make local development, testing, and demonstration easier.
"""
import base64
import time
from urllib.parse import urlencode

import jwt
import yaml
from flask import Blueprint, render_template, request, current_app, redirect, url_for

openid_blueprint = Blueprint(
    "openid", __name__, template_folder="templates", static_folder="static"
)

MY_SECRET_CODE = ":this_is_not_secure_do_not_use_in_production"


@openid_blueprint.route("/.well-known/openid-configuration", methods=["GET"])
def well_known():
    """OpenID Discovery endpoint -- as these urls can be very different from system to system,
       this is just a small subset."""
    host_url = request.host_url.strip('/')
    return {
        "issuer": f"{host_url}/openid",
        "authorization_endpoint": f"{host_url}{url_for('openid.auth')}",
        "token_endpoint": f"{host_url}{url_for('openid.token')}",
        "end_session_endpoint": f"{host_url}{url_for('openid.end_session')}",
    }


@openid_blueprint.route("/auth", methods=["GET"])
def auth():
    """Accepts a series of parameters"""
    return render_template('login.html',
                           state=request.args.get('state'),
                           response_type=request.args.get('response_type'),
                           client_id=request.args.get('client_id'),
                           scope=request.args.get('scope'),
                           redirect_uri=request.args.get('redirect_uri'),
                           error_message=request.args.get('error_message', ''))


@openid_blueprint.route("/form_submit", methods=["POST"])
def form_submit():
    users = get_users()
    if request.values['Uname'] in users and request.values['Pass'] == users[request.values['Uname']]["password"]:
        # Redirect back to the end user with some detailed information
        state = request.values.get('state')
        data = {
            "state": state,
            "code": request.values['Uname'] + MY_SECRET_CODE,
            "session_state": ""
        }
        url = request.values.get('redirect_uri') + "?" + urlencode(data)
        return redirect(url)
    else:
        return render_template('login.html',
                               state=request.values.get('state'),
                               response_type=request.values.get('response_type'),
                               client_id=request.values.get('client_id'),
                               scope=request.values.get('scope'),
                               redirect_uri=request.values.get('redirect_uri'),
                               error_message="Login failed.  Please try again.")


@openid_blueprint.route("/token", methods=["POST"])
def token():
    """Url that will return a valid token, given the super secret sauce"""
    grant_type = request.values.get('grant_type')
    code = request.values.get('code')
    redirect_uri = request.values.get('redirect_uri')

    """We just stuffed the user name on the front of the code, so grab it."""
    user_name, secret_hash = code.split(":")
    user_details = get_users()[user_name]

    """Get authentication from headers."""
    authorization = request.headers.get('Authorization')
    authorization = authorization[6:]  # Remove "Basic"
    authorization = base64.b64decode(authorization).decode('utf-8')
    client_id, client_secret = authorization.split(":")

    base_url = request.host_url + "openid"
    access_token = user_name + ":" + "always_good_demo_access_token"
    refresh_token = user_name + ":" + "always_good_demo_refresh_token"

    id_token = jwt.encode({
        "iss": base_url,
        "aud": [client_id, "account"],
        "iat": time.time(),
        "exp": time.time() + 86400,  # Expire after a day.
        "sub": user_name,
        "preferred_username": user_details.get('preferred_username', user_name)
    },
        client_secret,
        algorithm="HS256",
    )
    response = {
        "access_token": id_token,
        "id_token": id_token,
        "refresh_token": id_token
    }
    return response


@openid_blueprint.route("/end_session", methods=["GET"])
def end_session():
    redirect_url = request.args.get('post_logout_redirect_uri')
    id_token_hint = request.args.get('id_token_hint')
    return redirect(redirect_url)


@openid_blueprint.route("/refresh", methods=["POST"])
def refresh():
    pass


permission_cache = None


def get_users():
    global permission_cache
    if not permission_cache:
        with open(current_app.config["PERMISSIONS_FILE_FULLPATH"]) as file:
            permission_cache = yaml.safe_load(file)
    if "users" in permission_cache:
        return permission_cache["users"]
    else:
        return {}

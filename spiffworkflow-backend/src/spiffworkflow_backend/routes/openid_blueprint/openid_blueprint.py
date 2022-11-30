"""
Provides the bare minimum endpoints required by SpiffWorkflow to
handle openid authentication -- definitely not a production system.
This is just here to make local development, testing, and
demonstration easier.
"""
import base64
import time
import urllib
from urllib.parse import urlencode

import jwt
import yaml
from flask import Blueprint, render_template, request, current_app, redirect, url_for, g

openid_blueprint = Blueprint(
    "openid", __name__, template_folder="templates", static_folder="static"
)

MY_SECRET_CODE = ":this_should_be_some_crazy_code_different_all_the_time"

@openid_blueprint.route("/.well-known/openid-configuration", methods=["GET"])
def well_known():
    """OpenID Discovery endpoint -- as these urls can be very different from system to system,
       this is just a small subset."""
    host_url = request.host_url.strip('/')
    return {
        "issuer": f"{host_url}/openid",
        "authorization_endpoint":  f"{host_url}{url_for('openid.auth')}",
        "token_endpoint": f"{host_url}{url_for('openid.token')}",
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
                           error_message=request.args.get('error_message'))


@openid_blueprint.route("/form_submit", methods=["POST"])
def form_submit():

    users = get_users()
    if request.values['Uname'] in users and request.values['Pass'] == users[request.values['Uname']]["password"]:
        # Redirect back to the end user with some detailed information
        state = request.values.get('state')
        data = {
            "state": base64.b64encode(bytes(state, 'UTF-8')),
            "code": request.values['Uname'] + MY_SECRET_CODE,
            "session_state": ""
        }
        url = request.values.get('redirect_uri') + "?" + urlencode(data)
        return redirect(url, code=200)
    else:
        return render_template('login.html',
                               state=request.values.get('state'),
                               response_type=request.values.get('response_type'),
                               client_id=request.values.get('client_id'),
                               scope=request.values.get('scope'),
                               redirect_uri=request.values.get('redirect_uri'),
                               error_message="Login failed.  Please try agian.")


@openid_blueprint.route("/token", methods=["POST"])
def token():
    """Url that will return a valid token, given the super secret sauce"""
    grant_type=request.values.get('grant_type')
    code=request.values.get('code')
    redirect_uri=request.values.get('redirect_uri')

    """We just stuffed the user name on the front of the code, so grab it."""
    user_name, secret_hash = code.split(":")

    """Get authentication from headers."""
    authorization = request.headers.get('Authorization')
    authorization = authorization[6:]  # Remove "Basic"
    authorization = base64.b64decode(authorization).decode('utf-8')
    client_id, client_secret = authorization.split(":")

    base_url = url_for(openid_blueprint)
    access_token = "..."
    refresh_token = "..."
    id_token = jwt.encode({
        "iss": base_url,
        "aud": [client_id, "account"],
        "iat": time.time(),
        "exp": time.time() + 86400 # Exprire after a day.
    })

    {'exp': 1669757386, 'iat': 1669755586, 'auth_time': 1669753049, 'jti': '0ec2cc09-3498-4921-a021-c3b98427df70',
     'iss': 'http://localhost:7002/realms/spiffworkflow', 'aud': 'spiffworkflow-backend',
     'sub': '99e7e4ea-d4ae-4944-bd31-873dac7b004c', 'typ': 'ID', 'azp': 'spiffworkflow-backend',
     'session_state': '8751d5f6-2c60-4205-9be0-2b1005f5891e', 'at_hash': 'O5i-VLus6sryR0grMS2Y4w', 'acr': '0',
     'sid': '8751d5f6-2c60-4205-9be0-2b1005f5891e', 'email_verified': False, 'preferred_username': 'dan'}

    response = {
        "access_token": id_token,
        "id_token": id_token,
    }

@openid_blueprint.route("/refresh", methods=["POST"])
def refresh():
    pass

def get_users():
    with open(current_app.config["PERMISSIONS_FILE_FULLPATH"]) as file:
        permission_configs = yaml.safe_load(file)
    if "users" in permission_configs:
        return permission_configs["users"]
    else:
        return {}
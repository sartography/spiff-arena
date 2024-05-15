import sys

"""Get a token object for local development."""

import base64
import json

import requests

OPEN_ID_CODE = ":this_is_not_secure_do_not_use_in_production"
USER = "admin"
client_id = "spiffworkflow-backend"
client_secret = "JXeQExm0JhQPLumgHtIIqf52bDalHz0q"
redirect_uri = "http://localhost:7000/v1.0/login_return"
token_url = "http://localhost:7000/openid/token"


def get_auth_token_object() -> dict:
    backend_basic_auth_string = f"{client_id}:{client_secret}"
    backend_basic_auth_bytes = bytes(backend_basic_auth_string, encoding="ascii")
    backend_basic_auth = base64.b64encode(backend_basic_auth_bytes)
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {backend_basic_auth.decode('utf-8')}",
    }
    data = {
        "grant_type": "authorization_code",
        "code": USER + OPEN_ID_CODE,
        "redirect_uri": redirect_uri,
    }

    response = requests.post(token_url, data=data, headers=headers, timeout=15)
    auth_token_object: dict = json.loads(response.text)
    return auth_token_object


for token_identifier, token in get_auth_token_object().items():
    # if the k is access_token, print just it to stdout
    print(f"{token_identifier}:", file=sys.stderr)
    if token_identifier == "access_token":
        # print token with no newline
        print(token, end="")
        # flush the buffer to stdout
        sys.stdout.flush()
        print("\n", file=sys.stderr)
    else:
        # print the rest of the key value pairs to stderr
        print(f"{token}\n", file=sys.stderr)

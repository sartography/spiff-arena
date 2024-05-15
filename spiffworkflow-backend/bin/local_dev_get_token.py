"""
get a token object for local development
"""

import requests, base64, json

OPEN_ID_CODE = ":this_is_not_secure_do_not_use_in_production"
USER = "admin"
client_id = "spiffworkflow-backend"
client_secret = "JXeQExm0JhQPLumgHtIIqf52bDalHz0q"
redirect_uri = "http://localhost:7000/v1.0/login_return"
token_url = 'http://localhost:7000/openid/token'


def get_auth_token_object():
    backend_basic_auth_string = (
        f"{client_id}:{client_secret}"
    )
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


for k, v in get_auth_token_object().items():
    print(f"{k}: {v}")
    print('\n')

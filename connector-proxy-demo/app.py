import hmac
import os

from spiffworkflow_proxy.blueprint import proxy_blueprint
from flask import Flask
from flask import jsonify
from flask import request

CONNECTOR_PROXY_API_KEY_CONFIG = "SPIFF_CONNECTOR_PROXY_API_KEY"
CONNECTOR_PROXY_API_KEY_HEADER = "Spiff-Connector-Proxy-Api-Key"
CONNECTOR_PROXY_API_KEY_PROTECTED_PATHS = ("/v1/commands", "/v1/auths")
CONNECTOR_PROXY_API_KEY_PROTECTED_PREFIXES = ("/v1/do/",)

app = Flask(__name__)
app.config.from_pyfile("config.py", silent=True)
app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = os.environ.get(
    CONNECTOR_PROXY_API_KEY_CONFIG,
    app.config.get(CONNECTOR_PROXY_API_KEY_CONFIG),
)

if app.config.get("ENV", "development") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


@app.before_request
def require_connector_proxy_api_key():
    if not (
        request.path in CONNECTOR_PROXY_API_KEY_PROTECTED_PATHS
        or request.path.startswith(CONNECTOR_PROXY_API_KEY_PROTECTED_PREFIXES)
    ):
        return None

    expected_api_key = app.config.get(CONNECTOR_PROXY_API_KEY_CONFIG)
    if not expected_api_key:
        return None

    request_api_key = request.headers.get(CONNECTOR_PROXY_API_KEY_HEADER, "")
    if not hmac.compare_digest(request_api_key, expected_api_key):
        return jsonify({"error": "Unauthorized"}), 401

    return None

# Use the SpiffConnector Blueprint, which will auto-discover any
# connector-* packages and provide API endpoints for listing and executing
# available services.
app.register_blueprint(proxy_blueprint)

if __name__ == "__main__":
    app.run(host="localhost", port=7004)

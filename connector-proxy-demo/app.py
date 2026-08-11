import hmac
import os

from spiffworkflow_proxy.blueprint import proxy_blueprint
from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS

CONNECTOR_PROXY_API_KEY_CONFIG = "CONNECTOR_PROXY_API_KEY"
CONNECTOR_PROXY_API_KEY_HEADER = "Spiff-Connector-Proxy-Api-Key"
CONNECTOR_PROXY_API_KEY_PROTECTED_PATHS = ("/v1/commands", "/v1/auths")
CONNECTOR_PROXY_API_KEY_PROTECTED_PREFIXES = ("/v1/do/",)
CONNECTOR_PROXY_CORS_ORIGINS_CONFIG = "CONNECTOR_PROXY_CORS_ORIGINS"


class ConfigurationError(Exception):
    pass


def connector_proxy_api_key_config():
    return os.environ.get(
        CONNECTOR_PROXY_API_KEY_CONFIG,
        app.config.get(CONNECTOR_PROXY_API_KEY_CONFIG),
    )


def validate_connector_proxy_api_key(api_key):
    if api_key == "":
        raise ConfigurationError(
            f"{CONNECTOR_PROXY_API_KEY_CONFIG} config cannot be empty. Unset it to disable API key authentication."
        )
    return api_key


def connector_proxy_cors_origins_config():
    configured_origins = os.environ.get(
        CONNECTOR_PROXY_CORS_ORIGINS_CONFIG,
        app.config.get(CONNECTOR_PROXY_CORS_ORIGINS_CONFIG, ""),
    )
    if isinstance(configured_origins, str):
        return [origin.strip() for origin in configured_origins.split(",") if origin.strip()]
    return configured_origins


app = Flask(__name__)
app.config.from_pyfile("config.py", silent=True)
app.config[CONNECTOR_PROXY_API_KEY_CONFIG] = validate_connector_proxy_api_key(connector_proxy_api_key_config())
cors_origins = connector_proxy_cors_origins_config()
if cors_origins:
    CORS(
        app,
        resources={r"/v1/.*": {"origins": cors_origins}},
        allow_headers=["Content-Type", CONNECTOR_PROXY_API_KEY_HEADER],
    )

if app.config.get("ENV", "development") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"


@app.before_request
def require_connector_proxy_api_key():
    if request.method == "OPTIONS":
        return None

    if not (
        request.path in CONNECTOR_PROXY_API_KEY_PROTECTED_PATHS
        or request.path.startswith(CONNECTOR_PROXY_API_KEY_PROTECTED_PREFIXES)
    ):
        return None

    expected_api_key = validate_connector_proxy_api_key(app.config.get(CONNECTOR_PROXY_API_KEY_CONFIG))
    if expected_api_key is None:
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

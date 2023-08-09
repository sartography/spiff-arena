import os

from spiffworkflow_proxy.blueprint import proxy_blueprint
from flask import Flask

app = Flask(__name__)
app.config.from_pyfile("config.py", silent=True)

if app.config.get("ENV", "development") != "production":
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

# Use the SpiffConnector Blueprint, which will auto-discover any
# connector-* packages and provide API endpoints for listing and executing
# available services.
app.register_blueprint(proxy_blueprint)

if __name__ == "__main__":
    app.run(host="localhost", port=7004)

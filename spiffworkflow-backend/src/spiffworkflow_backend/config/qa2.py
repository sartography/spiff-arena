"""Qa2."""
from os import environ

SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME", default="qa1.yml"
)
SPIFFWORKFLOW_FRONTEND_URL = "https://qa2.spiffworkflow.org"
OPEN_ID_SERVER_URL = "https://qa2.spiffworkflow.org/keycloak/realms/spiffworkflow"
SPIFFWORKFLOW_BACKEND_URL = "https://qa2.spiffworkflow.org/api"
CONNECTOR_PROXY_URL = "https://qa2.spiffworkflow.org/connector-proxy"

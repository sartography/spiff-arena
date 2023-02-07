"""Qa2."""
from os import environ

SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME", default="qa1.yml"
)

OPEN_ID_SERVER_URL = "https://keycloak.qa1.spiffworkflow.org/realms/spiffworkflow"

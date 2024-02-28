from typing import Any

from flask import g
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.secret_service import SecretService


class SetSecret(Script):
    def get_description(self) -> str:
        return "Allows setting a secret value programmatically."

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if len(args) < 2:
            raise ValueError("Expected at least two arguments: secret_key and secret_value")
        if not hasattr(g, "user") or not g.user:
            raise RuntimeError("User context is not set")
        secret_key = args[0]
        secret_value = args[1]
        SecretService.update_secret(secret_key, secret_value, g.user.id, True)

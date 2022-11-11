"""Get_env."""
from typing import Any

from flask import current_app
from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


class GetFrontendUrl(Script):
    """GetFrontendUrl."""

    def get_description(self) -> str:
        """Get_description."""
        return """Return the url to the frontend."""

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any
    ) -> Any:
        """Run."""
        return current_app.config["SPIFFWORKFLOW_FRONTEND_URL"]

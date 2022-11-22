"""Get_process_info."""
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import (
    ScriptAttributesContext,
)
from spiffworkflow_backend.scripts.script import Script


class getDmn(Script):
    """Returns the requested DMN Table (provided as a decision id) as a list of dictionaries - one item
    per row."""

    def get_description(self) -> str:
        """Get_description."""
        return """Returns the requested DMN Table (provided as a decision id) as a list of dictionaries - one item
    per row. """

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *_args: Any,
        **kwargs: Any
    ) -> Any:

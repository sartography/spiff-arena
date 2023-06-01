from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class FactService(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Just your basic class that can pull in data from a few api endpoints and
        do a basic task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        if "type" not in kwargs:
            raise Exception("Please specify a 'type' of fact as a keyword argument.")
        else:
            fact = kwargs["type"]

        if fact == "cat":
            details = "The cat in the hat"  # self.get_cat()
        elif fact == "norris":
            details = "Chuck Norris doesn’t read books. He stares them down until he gets the information he wants."
        elif fact == "buzzword":
            details = "Move the Needle."  # self.get_buzzword()
        else:
            details = "unknown fact type."

        # self.add_data_to_task(task, details)
        return details

from datetime import datetime
from typing import Any

import pytz
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetLocaltime(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Converts a Datetime object into a Datetime object for a specific timezone.
        Defaults to US/Eastern."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> datetime:
        if len(args) > 0 or "datetime" in kwargs:
            if "datetime" in kwargs:
                date_time = kwargs["datetime"]
            else:
                date_time = args[0]
            if "timezone" in kwargs:
                timezone = kwargs["timezone"]
            elif len(args) > 1:
                timezone = args[1]
            else:
                timezone = "US/Eastern"
            localtime: datetime = date_time.astimezone(pytz.timezone(timezone))
            return localtime

        else:
            raise ApiError(
                error_code="missing_datetime",
                message="You must include a datetime to convert.",
            )

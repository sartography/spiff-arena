"""Get_localtime."""
from datetime import datetime
from typing import Any
from typing import Optional

import pytz
from flask_bpmn.api.api_error import ApiError
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.scripts.script import Script


class GetLocaltime(Script):
    """GetLocaltime."""

    def get_description(self) -> str:
        """Get_description."""
        return """Converts a Datetime object into a Datetime object for a specific timezone.
        Defaults to US/Eastern."""

    def run(
        self,
        task: Optional[SpiffTask],
        environment_identifier: str,
        *args: Any,
        **kwargs: Any
    ) -> datetime:
        """Run."""
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

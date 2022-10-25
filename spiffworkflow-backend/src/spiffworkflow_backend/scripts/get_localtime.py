from flask_bpmn.api.api_error import ApiError

from spiffworkflow_backend.scripts.script import Script

import pytz

from typing import Any
from typing import Optional

from SpiffWorkflow.task import Task as SpiffTask  # type: ignore


class GetLocaltime(Script):

    def get_description(self):
        return """Converts a Datetime object into a Datetime object for a specific timezone.
        Defaults to US/Eastern"""

    def run(
        self,
        task: Optional[SpiffTask],
        environment_identifier: str,
        *args: Any,
        **kwargs: Any
    ):
        if len(args) > 0 or 'datetime' in kwargs:
            if 'datetime' in kwargs:
                datetime = kwargs['datetime']
            else:
                datetime = args[0]
            if 'timezone' in kwargs:
                timezone = kwargs['timezone']
            elif len(args) > 1:
                timezone = args[1]
            else:
                timezone = 'US/Eastern'
            localtime = datetime.astimezone(pytz.timezone(timezone))
            return localtime

        else:
            raise ApiError(status_code='missing_datetime',
                           message='You must include a datetime to convert.')

from typing import Any

from spiffworkflow_connector_command.command_interface import CommandErrorDict
from spiffworkflow_connector_command.command_interface import CommandResponseDict
from spiffworkflow_connector_command.command_interface import ConnectorCommand
from spiffworkflow_connector_command.command_interface import ConnectorProxyResponseDict


class Example(ConnectorCommand):
    def __init__(self,
        message: str,
    ):
        self.message = message

    def execute(self, _config: Any, _task_data: Any) -> ConnectorProxyResponseDict:
        error: CommandErrorDict | None = None

        return_response: CommandResponseDict = {
            "body": {
                "connector_response": f"You passed the example connector: '{self.message}'. Have a good day!",
            },
            "mimetype": "application/json",
        }

        result: ConnectorProxyResponseDict = {
            "command_response": return_response,
            "error": error,
            "command_response_version": 2,
            "spiff__logs": [],
        }

        return result

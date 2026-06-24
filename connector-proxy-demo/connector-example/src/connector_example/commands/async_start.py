import json
import threading
import time
from typing import Any
from urllib import request

from spiffworkflow_connector_command.command_interface import CommandErrorDict
from spiffworkflow_connector_command.command_interface import CommandResponseDict
from spiffworkflow_connector_command.command_interface import ConnectorCommand
from spiffworkflow_connector_command.command_interface import ConnectorProxyResponseDict


class AsyncStart(ConnectorCommand):
    def __init__(
        self,
        mode: str = "accepted",
        message: str = "async connector accepted the work",
        complete_callback: bool = False,
        callback_delay_seconds: int = 2,
    ):
        self.mode = mode
        self.message = message
        self.complete_callback = complete_callback
        self.callback_delay_seconds = callback_delay_seconds

    def execute(self, _config: Any, _task_data: Any) -> ConnectorProxyResponseDict:
        return self._response(
            body={"accepted": False, "message": "AsyncStart requires a spiff__callback_url."},
            error={
                "error_code": "AsyncConnectorMissingCallbackUrl",
                "message": "AsyncStart must be called with a callback URL.",
            },
            http_status=400,
        )

    def execute_async(self, _config: Any, _task_data: Any, callback_url: str) -> ConnectorProxyResponseDict:
        if self.mode == "error":
            return self._response(
                body={"accepted": False, "mode": self.mode, "message": self.message},
                error={
                    "error_code": "AsyncConnectorRejected",
                    "message": self.message,
                },
                http_status=400,
            )

        if self.complete_callback:
            self._schedule_callback(callback_url)

        return self._response(
            body={
                "accepted": True,
                "mode": self.mode,
                "message": self.message,
                "callback_scheduled": self.complete_callback,
            },
            error=None,
            http_status=202,
        )

    def _response(
        self,
        body: dict[str, Any],
        error: CommandErrorDict | None,
        http_status: int,
    ) -> ConnectorProxyResponseDict:
        return_response: CommandResponseDict = {
            "body": body,
            "mimetype": "application/json",
            "http_status": http_status,
        }

        return {
            "command_response": return_response,
            "error": error,
            "command_response_version": 2,
            "spiff__logs": [f"AsyncStart mode={self.mode} http_status={http_status}"],
        }

    def _schedule_callback(self, callback_url: str) -> None:
        callback_delay_seconds = max(int(self.callback_delay_seconds), 0)
        thread = threading.Thread(
            target=self._send_callback,
            args=(callback_url, callback_delay_seconds),
            daemon=True,
        )
        thread.start()

    def _send_callback(self, callback_url: str, callback_delay_seconds: int) -> None:
        time.sleep(callback_delay_seconds)
        callback_payload = {
            "command_response": {
                "body": {
                    "completed": True,
                    "message": self.message,
                },
                "mimetype": "application/json",
            },
            "command_response_version": 2,
            "error": None,
        }
        body = json.dumps(callback_payload).encode("utf-8")
        callback_request = request.Request(
            callback_url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="PUT",
        )
        request.urlopen(callback_request, timeout=30).read()

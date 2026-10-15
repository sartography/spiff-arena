from unittest.mock import patch

from flask import Flask
from prometheus_client import REGISTRY

from spiffworkflow_backend.services.message_instrumentation_service import log_message_send_expired


def test_expiry_logging_failure_does_not_interrupt_message_handling(app: Flask) -> None:
    labels = {"reason": "no_waiting_receiver"}
    before = REGISTRY.get_sample_value("spiff_message_send_expired_total", labels) or 0.0
    with patch.object(app.logger, "info", side_effect=RuntimeError("logging unavailable")):
        log_message_send_expired("reply", 1, None, "no_waiting_receiver")
    assert REGISTRY.get_sample_value("spiff_message_send_expired_total", labels) == before + 1


def test_expiry_logging_survives_metric_failure(app: Flask) -> None:
    with (
        patch(
            "spiffworkflow_backend.services.message_instrumentation_service.MESSAGE_SEND_EXPIRED_TOTAL.labels",
            side_effect=RuntimeError("metrics unavailable"),
        ),
        patch.object(app.logger, "info") as log,
    ):
        log_message_send_expired("reply", 1, None, "no_waiting_receiver")
    log.assert_called_once()
    assert log.call_args.kwargs["extra"]["extras"] == {
        "event_name": "message_send_expired",
        "reason": "no_waiting_receiver",
        "message_name": "reply",
        "message_instance_id": 1,
        "message_instance_uuid": None,
    }

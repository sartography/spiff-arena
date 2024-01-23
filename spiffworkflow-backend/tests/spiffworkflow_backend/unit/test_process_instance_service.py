import base64
import hashlib
from datetime import datetime
from datetime import timezone
from typing import Any

import pytest
from flask.app import Flask
from SpiffWorkflow.bpmn.event import PendingBpmnEvent  # type: ignore
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


def _file_content(i: int) -> bytes:
    return f"testing{i}\n".encode()


def _file_data(i: int) -> str:
    b64 = base64.b64encode(_file_content(i)).decode()
    return f"data:some/mimetype;name=testing{i}.txt;base64,{b64}"


def _digest(i: int) -> str:
    return hashlib.sha256(_file_content(i)).hexdigest()


def _digest_reference(i: int) -> str:
    sha = _digest(i)
    b64 = f"{ProcessInstanceService.FILE_DATA_DIGEST_PREFIX}{sha}"
    return f"data:some/mimetype;name=testing{i}.txt;base64,{b64}"


class TestProcessInstanceService(BaseTest):
    @pytest.mark.parametrize(
        "data,expected_data,expected_models_len",
        [
            ({}, {}, 0),
            ({"k": "v"}, {"k": "v"}, 0),
            ({"k": _file_data(0)}, {"k": _digest_reference(0)}, 1),
            ({"k": [_file_data(0)]}, {"k": [_digest_reference(0)]}, 1),
            ({"k": [_file_data(0), _file_data(1)]}, {"k": [_digest_reference(0), _digest_reference(1)]}, 2),
            ({"k": [{"k2": _file_data(0)}]}, {"k": [{"k2": _digest_reference(0)}]}, 1),
            (
                {"k": [{"k2": _file_data(0)}, {"k2": _file_data(1)}, {"k2": _file_data(2)}]},
                {"k": [{"k2": _digest_reference(0)}, {"k2": _digest_reference(1)}, {"k2": _digest_reference(2)}]},
                3,
            ),
            ({"k": [{"k2": _file_data(0), "k3": "bob"}]}, {"k": [{"k2": _digest_reference(0), "k3": "bob"}]}, 1),
            (
                {"k": [{"k2": _file_data(0), "k3": "bob"}, {"k2": _file_data(1), "k3": "bob"}]},
                {"k": [{"k2": _digest_reference(0), "k3": "bob"}, {"k2": _digest_reference(1), "k3": "bob"}]},
                2,
            ),
            (
                {
                    "k": [
                        {
                            "k2": [
                                {"k3": [_file_data(0)]},
                                {"k4": {"k5": {"k6": [_file_data(1), _file_data(2)], "k7": _file_data(3)}}},
                            ]
                        }
                    ]
                },
                {
                    "k": [
                        {
                            "k2": [
                                {"k3": [_digest_reference(0)]},
                                {"k4": {"k5": {"k6": [_digest_reference(1), _digest_reference(2)], "k7": _digest_reference(3)}}},
                            ]
                        }
                    ]
                },
                4,
            ),
        ],
    )
    def test_save_file_data_v0(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        data: dict[str, Any],
        expected_data: dict[str, Any],
        expected_models_len: int,
    ) -> None:
        process_instance_id = 123
        models = ProcessInstanceService.replace_file_data_with_digest_references(
            data,
            process_instance_id,
        )

        assert data == expected_data
        assert len(models) == expected_models_len

        for i, model in enumerate(models):
            assert model.process_instance_id == process_instance_id
            assert model.mimetype == "some/mimetype"
            assert model.filename == f"testing{i}.txt"
            assert model.contents == _file_content(i)  # type: ignore
            assert model.digest == _digest(i)

    def test_does_not_skip_events_it_does_not_know_about(self) -> None:
        name = None
        event_type = "Unknown"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert not (
            ProcessInstanceService.waiting_event_can_be_skipped(
                pending_event,
                datetime.now(timezone.utc),
            )
        )

    def test_does_skip_duration_timer_events_for_the_future(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert ProcessInstanceService.waiting_event_can_be_skipped(
            pending_event,
            datetime.fromisoformat("2023-04-26T20:15:10.626656+00:00"),
        )

    def test_does_not_skip_duration_timer_events_for_the_past(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert not (
            ProcessInstanceService.waiting_event_can_be_skipped(
                pending_event,
                datetime.fromisoformat("2023-04-28T20:15:10.626656+00:00"),
            )
        )

    def test_does_not_skip_duration_timer_events_for_now(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert not (
            ProcessInstanceService.waiting_event_can_be_skipped(
                pending_event,
                datetime.fromisoformat("2023-04-27T20:15:10.626656+00:00"),
            )
        )

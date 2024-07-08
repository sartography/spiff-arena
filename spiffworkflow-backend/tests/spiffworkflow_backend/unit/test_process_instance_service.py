import base64
import hashlib
import os
from datetime import datetime
from datetime import timezone
from typing import Any

import pytest
from flask.app import Flask
from SpiffWorkflow.bpmn.util import PendingBpmnEvent  # type: ignore
from spiffworkflow_backend.exceptions.error import ProcessInstanceMigrationNotSafeError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.spec_file_service import SpecFileService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


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
            assert model.contents == _file_content(i)
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

    def test_it_can_migrate_a_process_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/migration-test-with-subprocess",
            process_model_source_directory="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        initial_tasks = processor.bpmn_process_instance.get_tasks()
        assert "manual_task_two" not in processor.bpmn_process_instance.spec.task_specs

        new_file_path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "migration-test-with-subprocess",
            "migration-new.bpmn",
        )
        with open(new_file_path) as f:
            new_contents = f.read().encode()

        SpecFileService.update_file(
            process_model_info=process_model,
            file_name="migration-initial.bpmn",
            binary_data=new_contents,
            update_process_cache_only=True,
        )

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        ProcessInstanceService.migrate_process_instance_to_newest_model_version(process_instance, user=initiator_user)

        for initial_task in initial_tasks:
            new_task = processor.bpmn_process_instance.get_task_from_id(initial_task.id)
            assert new_task is not None
            assert new_task.last_state_change == initial_task.last_state_change

        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"
        self.complete_next_manual_task(processor)

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_two"
        self.complete_next_manual_task(processor)

        assert process_instance.status == ProcessInstanceStatus.complete.value

    def test_it_can_check_if_a_process_instance_can_be_migrated(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/migration-test-with-subprocess",
            process_model_source_directory="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        new_file_path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "migration-test-with-subprocess",
            "migration-new.bpmn",
        )
        with open(new_file_path) as f:
            new_contents = f.read().encode()

        SpecFileService.update_file(
            process_model_info=process_model,
            file_name="migration-initial.bpmn",
            binary_data=new_contents,
            update_process_cache_only=True,
        )

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        ProcessInstanceService.check_process_instance_can_be_migrated(process_instance)

    def test_it_raises_if_a_process_instance_cannot_be_migrated_to_new_process_model_version(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/migration-test-with-subprocess",
            process_model_source_directory="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"
        self.complete_next_manual_task(processor)
        assert process_instance.status == ProcessInstanceStatus.complete.value

        new_file_path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "migration-test-with-subprocess",
            "migration-new.bpmn",
        )
        with open(new_file_path) as f:
            new_contents = f.read().encode()

        SpecFileService.update_file(
            process_model_info=process_model,
            file_name="migration-initial.bpmn",
            binary_data=new_contents,
            update_process_cache_only=True,
        )

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()

        with pytest.raises(ProcessInstanceMigrationNotSafeError):
            ProcessInstanceService.check_process_instance_can_be_migrated(process_instance)

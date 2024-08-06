import base64
import datetime
import hashlib
import os
from typing import Any

import pytest
from flask.app import Flask
from pytest_mock.plugin import MockerFixture
from SpiffWorkflow.bpmn.util import PendingBpmnEvent  # type: ignore
from spiffworkflow_backend.exceptions.error import ProcessInstanceMigrationNotSafeError
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.git_service import GitService
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
                datetime.datetime.now(datetime.timezone.utc),
            )
        )

    def test_does_skip_duration_timer_events_for_the_future(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert ProcessInstanceService.waiting_event_can_be_skipped(
            pending_event,
            datetime.datetime.fromisoformat("2023-04-26T20:15:10.626656+00:00"),
        )

    def test_does_not_skip_duration_timer_events_for_the_past(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert not (
            ProcessInstanceService.waiting_event_can_be_skipped(
                pending_event,
                datetime.datetime.fromisoformat("2023-04-28T20:15:10.626656+00:00"),
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
                datetime.datetime.fromisoformat("2023-04-27T20:15:10.626656+00:00"),
            )
        )

    def test_it_can_migrate_a_process_instance(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/migration-test-with-subprocess",
            process_model_source_directory="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        mock_get_current_revision = mocker.patch.object(GitService, "get_current_revision")

        # Set the return value for the first call
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user, bpmn_version_control_identifier="rev1"
        )
        assert process_instance.bpmn_version_control_identifier == "rev1"
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        initial_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        assert initial_bpmn_process_hash is not None

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"
        assert human_task_one.task_title == "Manual Task 1"
        assert human_task_one.task_name == "manual_task_one"

        initial_tasks = processor.bpmn_process_instance.get_tasks()
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_two", processor.bpmn_process_instance)
        assert spiff_task is None

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
        mock_get_current_revision.return_value = "rev2"
        ProcessInstanceService.migrate_process_instance(process_instance, user=initiator_user)

        # there should only be 5 events after the migration. anymore indicates that events are getting duplicated.
        process_instance_events = ProcessInstanceEventModel.query.filter_by(process_instance_id=process_instance.id).all()
        # NOTE: this would be 5 but for some reason we are not storing the event for the spiff created subprocess start task
        assert len(process_instance_events) == 4

        for initial_task in initial_tasks:
            new_task = processor.bpmn_process_instance.get_task_from_id(initial_task.id)
            assert new_task is not None
            assert new_task.last_state_change == initial_task.last_state_change

        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"
        assert human_task_one.task_title == "Manual Task One"
        self.complete_next_manual_task(processor)

        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_two"
        self.complete_next_manual_task(processor)

        assert process_instance.status == ProcessInstanceStatus.complete.value

        target_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        assert target_bpmn_process_hash is not None
        assert initial_bpmn_process_hash != target_bpmn_process_hash

        pi_events = ProcessInstanceEventModel.query.filter_by(
            process_instance_id=process_instance.id, event_type=ProcessInstanceEventType.process_instance_migrated.value
        ).all()
        assert len(pi_events) == 1
        process_instance_event = pi_events[0]
        assert len(process_instance_event.migration_details) == 1
        pi_migration_details = process_instance_event.migration_details[0]

        assert pi_migration_details.initial_bpmn_process_hash == initial_bpmn_process_hash
        assert pi_migration_details.target_bpmn_process_hash == target_bpmn_process_hash
        assert pi_migration_details.initial_git_revision == "rev1"
        assert pi_migration_details.target_git_revision == "rev2"
        assert process_instance.bpmn_version_control_identifier == "rev2"

    def test_it_can_migrate_a_process_instance_and_revert(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/migration-test-with-subprocess",
            process_model_source_directory="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        mock_get_current_revision = mocker.patch.object(GitService, "get_current_revision")

        # Set the return value for the first call
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user, bpmn_version_control_identifier="rev1"
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        initial_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        assert initial_bpmn_process_hash is not None

        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_two", processor.bpmn_process_instance)
        assert spiff_task is None

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
        mock_get_current_revision.return_value = "rev2"
        ProcessInstanceService.migrate_process_instance(process_instance, user=initiator_user)
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        assert process_instance.bpmn_version_control_identifier == "rev2"
        target_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_two", processor.bpmn_process_instance)
        assert spiff_task is not None

        ProcessInstanceService.migrate_process_instance(
            process_instance, user=initiator_user, target_bpmn_process_hash=initial_bpmn_process_hash
        )
        processor = ProcessInstanceProcessor(process_instance)
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_two", processor.bpmn_process_instance)
        assert spiff_task is None
        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"
        self.complete_next_manual_task(processor)
        assert process_instance.status == ProcessInstanceStatus.complete.value

        pi_events = (
            ProcessInstanceEventModel.query.filter_by(
                process_instance_id=process_instance.id, event_type=ProcessInstanceEventType.process_instance_migrated.value
            )
            .order_by(ProcessInstanceEventModel.id)
            .all()
        )
        assert len(pi_events) == 2

        process_instance_event = pi_events[0]
        assert len(process_instance_event.migration_details) == 1
        pi_migration_details = process_instance_event.migration_details[0]
        assert pi_migration_details.initial_bpmn_process_hash == initial_bpmn_process_hash
        assert pi_migration_details.target_bpmn_process_hash == target_bpmn_process_hash
        assert pi_migration_details.initial_git_revision == "rev1"
        assert pi_migration_details.target_git_revision == "rev2"

        process_instance_event = pi_events[1]
        assert len(process_instance_event.migration_details) == 1
        pi_migration_details = process_instance_event.migration_details[0]
        assert pi_migration_details.initial_bpmn_process_hash == target_bpmn_process_hash
        assert pi_migration_details.target_bpmn_process_hash == initial_bpmn_process_hash
        assert pi_migration_details.initial_git_revision == "rev2"
        assert pi_migration_details.target_git_revision == "rev1"
        assert process_instance.bpmn_version_control_identifier == "rev1"

    def test_it_can_migrate_a_process_instance_multiple_times_and_revert(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/migration-test-with-subprocess",
            process_model_source_directory="migration-test-with-subprocess",
            bpmn_file_name="migration-initial.bpmn",
        )
        mock_get_current_revision = mocker.patch.object(GitService, "get_current_revision")

        # Set the return value for the first call
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user, bpmn_version_control_identifier="rev1"
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        initial_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        assert initial_bpmn_process_hash is not None

        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_two", processor.bpmn_process_instance)
        assert spiff_task is None

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
        mock_get_current_revision.return_value = "rev2"
        ProcessInstanceService.migrate_process_instance(process_instance, user=initiator_user)
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        assert process_instance.bpmn_version_control_identifier == "rev2"
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        target_bpmn_process_hash_one = process_instance.bpmn_process_definition.full_process_model_hash
        assert target_bpmn_process_hash_one is not None
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_two", processor.bpmn_process_instance)
        assert spiff_task is not None

        new_file_path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "migration-test-with-subprocess",
            "migration-new-2.bpmn",
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
        mock_get_current_revision.return_value = "rev3"
        ProcessInstanceService.migrate_process_instance(process_instance, user=initiator_user)
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        assert process_instance.bpmn_version_control_identifier == "rev3"
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        target_bpmn_process_hash_two = process_instance.bpmn_process_definition.full_process_model_hash
        assert target_bpmn_process_hash_two is not None
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_three", processor.bpmn_process_instance)
        assert spiff_task is not None

        ProcessInstanceService.migrate_process_instance(
            process_instance, user=initiator_user, target_bpmn_process_hash=initial_bpmn_process_hash
        )
        processor = ProcessInstanceProcessor(process_instance)
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("manual_task_two", processor.bpmn_process_instance)
        assert spiff_task is None
        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_model.task_definition.bpmn_identifier == "manual_task_one"
        self.complete_next_manual_task(processor)
        assert process_instance.status == ProcessInstanceStatus.complete.value

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        assert process_instance.bpmn_version_control_identifier == "rev1"

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

    def test_it_can_migrate_a_process_instance_a_timer(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/migration-test-with-timer",
            process_model_source_directory="migration-test-with-timer",
            bpmn_file_name="migration-initial.bpmn",
        )
        mock_get_current_revision = mocker.patch.object(GitService, "get_current_revision")

        # Set the return value for the first call
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user, bpmn_version_control_identifier="rev1"
        )
        assert process_instance.bpmn_version_control_identifier == "rev1"
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        initial_bpmn_process_hash = process_instance.bpmn_process_definition.full_process_model_hash
        assert initial_bpmn_process_hash is not None

        ready_tasks = processor.get_all_ready_or_waiting_tasks()
        assert len(ready_tasks) == 1
        assert ready_tasks[0].task_spec.name == "TimerEvent1"
        task = TaskModel.query.filter_by(guid=str(ready_tasks[0].id)).first()
        assert task is not None
        self.set_timer_event_to_new_time(task, {"seconds": 50})

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        ready_tasks = processor.get_all_ready_or_waiting_tasks()
        assert len(ready_tasks) == 2
        ready_task_names = [t.task_spec.name for t in ready_tasks]
        assert sorted(ready_task_names) == ["Test_Timer_intermediate_catch.EndJoin", "TimerEvent1"]

        timer_event_spiff_task = next(t for t in ready_tasks if t.task_spec.name == "TimerEvent1")
        assert timer_event_spiff_task is not None
        timer_event_children = self.get_all_children_of_spiff_task(timer_event_spiff_task)
        timer_event_children_guids = [str(t.id) for t in timer_event_children]
        assert len(timer_event_children_guids) == 5

        new_file_path = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            "migration-test-with-timer",
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
        mock_get_current_revision.return_value = "rev2"
        ProcessInstanceService.migrate_process_instance(process_instance, user=initiator_user)

        child_task_models = TaskModel.query.filter(TaskModel.guid.in_(timer_event_children_guids)).all()  # type: ignore
        assert len(child_task_models) == 0
        timer_event_task_model = TaskModel.query.filter_by(guid=str(timer_event_spiff_task.id)).first()
        assert timer_event_task_model is not None
        # make sure it resets the cycles properly
        assert timer_event_task_model.properties_json["internal_data"]["event_value"]["cycles"] == 2

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

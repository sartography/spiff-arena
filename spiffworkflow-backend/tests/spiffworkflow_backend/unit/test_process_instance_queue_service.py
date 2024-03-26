import time
from contextlib import suppress

import pytest
from flask.app import Flask
from pytest_mock.plugin import MockerFixture
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_lock_service import ProcessInstanceLockService
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstanceQueueService(BaseTest):
    def _create_process_instance(self) -> ProcessInstanceModel:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        return process_instance

    def test_newly_created_process_instances_are_not_locked_when_added_to_the_queue(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()
        assert not ProcessInstanceLockService.has_lock(process_instance.id)
        queue_entries = ProcessInstanceQueueService.entries_with_status("not_started", None, round(time.time()))
        check_passed = False
        for entry in queue_entries:
            if entry.process_instance_id == process_instance.id:
                assert entry.locked_by is None
                check_passed = True
                break
        assert check_passed

    def test_peek_many_can_see_queue_entries_with_a_given_status(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()
        queue_entry_ids = ProcessInstanceQueueService.peek_many("not_started", round(time.time()))
        assert process_instance.id in queue_entry_ids

    def test_can_run_some_code_with_a_dequeued_process_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()
        check_passed = False
        with ProcessInstanceQueueService.dequeued(process_instance):
            check_passed = True
        assert check_passed

    def test_holds_a_lock_for_dequeued_process_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()
        assert not ProcessInstanceLockService.has_lock(process_instance.id)
        with ProcessInstanceQueueService.dequeued(process_instance):
            assert ProcessInstanceLockService.has_lock(process_instance.id)
        assert not ProcessInstanceLockService.has_lock(process_instance.id)

    def test_unlocks_if_an_exception_is_thrown_with_a__dequeued_process_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()

        with suppress(Exception):
            with ProcessInstanceQueueService.dequeued(process_instance):
                assert ProcessInstanceLockService.has_lock(process_instance.id)
                raise Exception("just testing")

        assert not ProcessInstanceLockService.has_lock(process_instance.id)

    def test_can_call_dequeued_mulitple_times(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()

        with ProcessInstanceQueueService.dequeued(process_instance):
            assert ProcessInstanceLockService.has_lock(process_instance.id)

        with ProcessInstanceQueueService.dequeued(process_instance):
            assert ProcessInstanceLockService.has_lock(process_instance.id)

        with ProcessInstanceQueueService.dequeued(process_instance):
            assert ProcessInstanceLockService.has_lock(process_instance.id)

    def test_can_nest_multiple_dequeued_calls(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()

        with ProcessInstanceQueueService.dequeued(process_instance):
            with ProcessInstanceQueueService.dequeued(process_instance):
                with ProcessInstanceQueueService.dequeued(process_instance):
                    assert ProcessInstanceLockService.has_lock(process_instance.id)

                assert ProcessInstanceLockService.has_lock(process_instance.id)
            assert ProcessInstanceLockService.has_lock(process_instance.id)

        assert not ProcessInstanceLockService.has_lock(process_instance.id)

    def test_dequeue_with_retries_works(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_instance = self._create_process_instance()
        dequeue_mocker = mocker.patch.object(
            ProcessInstanceQueueService, "_dequeue", side_effect=ProcessInstanceIsAlreadyLockedError
        )
        mocker.patch("time.sleep")
        with pytest.raises(ProcessInstanceIsAlreadyLockedError):
            with ProcessInstanceQueueService.dequeued(process_instance, max_attempts=5):
                pass
        assert dequeue_mocker.call_count == 5

        with pytest.raises(ProcessInstanceIsAlreadyLockedError):
            with ProcessInstanceQueueService.dequeued(process_instance):
                pass
        assert dequeue_mocker.call_count == 6

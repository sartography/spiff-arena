import time

from flask import Flask
from pytest_mock.plugin import MockerFixture

from spiffworkflow_backend.background_processing import CELERY_TASK_EVENT_NOTIFIER
from spiffworkflow_backend.background_processing.background_processing_service import BackgroundProcessingService
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestBackgroundProcessingService(BaseTest):
    def test_process_future_tasks_with_no_future_tasks(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        BackgroundProcessingService(app).process_future_tasks()

    def test_do_process_future_tasks_with_processable_future_task(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            mock = mocker.patch("celery.current_app.send_task")
            self._load_up_a_future_task_and_return_instance()
            assert mock.call_count == 0
            BackgroundProcessingService.do_process_future_tasks(99999999999999999)
            assert mock.call_count == 1
            future_tasks = FutureTaskModel.query.all()
            assert len(future_tasks) == 1
            assert future_tasks[0].archived_for_process_instance_status is False

    def test_do_process_future_tasks_with_unprocessable_future_task(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            mock = mocker.patch("celery.current_app.send_task")
            process_instance = self._load_up_a_future_task_and_return_instance()
            assert mock.call_count == 0
            process_instance.status = "suspended"
            db.session.add(process_instance)
            db.session.commit()
            future_tasks = BackgroundProcessingService.imminent_future_tasks(99999999999999999)
            assert len(future_tasks) == 1
            BackgroundProcessingService.do_process_future_tasks(99999999999999999)
            # should not process anything, so nothing goes to queue
            assert mock.call_count == 0
            future_tasks = FutureTaskModel.query.all()
            assert len(future_tasks) == 1
            assert future_tasks[0].archived_for_process_instance_status is True

            # the next time do_process_future_tasks runs, it will not consider this task, which is nice
            future_tasks = BackgroundProcessingService.imminent_future_tasks(99999999999999999)
            assert len(future_tasks) == 0
            processor = ProcessInstanceProcessor(process_instance)
            processor.resume()
            future_tasks = BackgroundProcessingService.imminent_future_tasks(99999999999999999)
            assert len(future_tasks) == 1

    def test_do_waiting_errors_gracefully_when_instance_already_locked(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, status="waiting")
        assert process_instance.status == ProcessInstanceStatus.waiting.value
        queue_entry = ProcessInstanceQueueModel.query.filter_by(process_instance_id=process_instance.id).first()
        assert queue_entry is not None
        queue_entry.locked_by = "test:test_waiting"
        queue_entry.locked_at_seconds = round(time.time())
        db.session.add(queue_entry)
        db.session.commit()

        mocker.patch.object(ProcessInstanceQueueService, "peek_many", return_value=[process_instance.id])
        ProcessInstanceService.do_waiting(ProcessInstanceStatus.waiting.value)
        assert process_instance.status == ProcessInstanceStatus.waiting.value

    def test_does_not_queue_future_tasks_if_requested(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            mock = mocker.patch("celery.current_app.send_task")
            self._load_up_a_future_task_and_return_instance(should_schedule_waiting_timer_events=False)
            assert mock.call_count == 0
            BackgroundProcessingService.do_process_future_tasks(99999999999999999)
            assert mock.call_count == 0
            future_tasks = FutureTaskModel.query.all()
            assert len(future_tasks) == 0

    def test_does_not_requeue_if_recently_queued(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            mock = mocker.patch("celery.current_app.send_task")
            assert mock.call_count == 0
            process_model = load_test_spec(
                process_model_id="test_group/user-task-with-timer",
                process_model_source_directory="user-task-with-timer",
                bpmn_file_name="user_task_with_short_timer.bpmn",
            )

            # it should queue only when it runs the process model
            self._load_up_a_future_task_and_return_instance(process_model=process_model)
            assert mock.call_count == 1
            BackgroundProcessingService.do_process_future_tasks(99999999999999999)
            assert mock.call_count == 1
            future_tasks = FutureTaskModel.query.all()
            assert len(future_tasks) == 1
            assert future_tasks[0].archived_for_process_instance_status is False

            BackgroundProcessingService.do_process_future_tasks(99999999999999999)
            assert mock.call_count == 1
            future_tasks = FutureTaskModel.query.all()
            assert len(future_tasks) == 1
            assert future_tasks[0].archived_for_process_instance_status is False

    def test_queues_event_notifier_when_new_human_task(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_EVENT_NOTIFIER_PROCESS_MODEL", "SOME PROCESS MODEL"):
                mock = mocker.patch("celery.current_app.send_task")
                process_model = load_test_spec(
                    process_model_id="group/multiinstance_manual_task",
                    process_model_source_directory="multiinstance_manual_task",
                )
                process_instance = self.create_process_instance_from_process_model(process_model=process_model)
                processor = ProcessInstanceProcessor(process_instance)
                processor.do_engine_steps(save=True)
                mock.assert_called_with(
                    CELERY_TASK_EVENT_NOTIFIER,
                    (process_instance.id, process_instance.process_model_identifier, "human_tasks_changed"),
                )
                assert mock.call_count == 1

    def test_queues_event_notifier_when_complete(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_EVENT_NOTIFIER_PROCESS_MODEL", "SOME PROCESS MODEL"):
                mock = mocker.patch("celery.current_app.send_task")
                process_model = load_test_spec(
                    "test_group/sample",
                    process_model_source_directory="sample",
                )
                process_instance = self.create_process_instance_from_process_model(
                    process_model=process_model, save_start_and_end_times=False
                )
                processor = ProcessInstanceProcessor(process_instance)
                processor.do_engine_steps(save=True)
                mock.assert_called_with(
                    CELERY_TASK_EVENT_NOTIFIER,
                    (process_instance.id, process_instance.process_model_identifier, "process_instance_complete"),
                )
                assert mock.call_count == 1

    def _load_up_a_future_task_and_return_instance(
        self, process_model: ProcessModelInfo | None = None, should_schedule_waiting_timer_events: bool = True
    ) -> ProcessInstanceModel:
        process_model_to_use = process_model
        if process_model_to_use is None:
            process_model_to_use = load_test_spec(
                process_model_id="test_group/user-task-with-timer",
                process_model_source_directory="user-task-with-timer",
                bpmn_file_name="user_task_with_timer.bpmn",
            )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model_to_use)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, should_schedule_waiting_timer_events=should_schedule_waiting_timer_events)

        assert process_instance.status == "user_input_required"

        future_tasks = FutureTaskModel.query.all()
        assert len(future_tasks) == (1 if should_schedule_waiting_timer_events else 0)
        return process_instance

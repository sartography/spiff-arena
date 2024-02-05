from flask import Flask
from pytest_mock.plugin import MockerFixture
from spiffworkflow_backend.background_processing.background_processing_service import BackgroundProcessingService
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.future_task import FutureTaskModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

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

    def _load_up_a_future_task_and_return_instance(self) -> ProcessInstanceModel:
        process_model = load_test_spec(
            process_model_id="test_group/user-task-with-timer",
            process_model_source_directory="user-task-with-timer",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert process_instance.status == "user_input_required"

        future_tasks = FutureTaskModel.query.all()
        assert len(future_tasks) == 1
        return process_instance

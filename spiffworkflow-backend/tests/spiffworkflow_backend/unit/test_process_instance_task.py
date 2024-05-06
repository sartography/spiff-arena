from unittest.mock import patch
from pytest_mock.plugin import MockerFixture
from flask.app import Flask
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task import celery_task_process_instance_run

# from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
#     queue_future_task_if_appropriate,
# )
from spiffworkflow_backend.models.db import db
import time
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessInstanceTask(BaseTest):
    def test_queues_process_instance_if_locked(
        self,
        app: Flask,
        mocker: MockerFixture,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            # mocked_process = mocker.Mock()
            # mocked_process.index = 12345  # Setting the pid attribute to a mock value
            # mocker.patch("billiard.current_process", return_value=mocked_process)

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
            # mocker.patch(
            #     "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer.queue_future_task_if_appropriate"
            # )

            with patch(
                "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task.get_current_process_index"
            ) as mock_proc_index:
                mock_proc_index.return_value = 1
                # with patch(
                #     "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer.queue_future_task_if_appropriate"
                # ) as mock_queue:
                with patch(
                    "spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer.queue_future_task_if_appropriate"
                ) as mock_queue:
                    mock_queue.return_value = 1
                    # mock = mocker.patch("billiard.current_process()", return_value=0)
                    celery_task_process_instance_run(process_instance_id=process_instance.id)
                    assert mock_queue.call_count == 1

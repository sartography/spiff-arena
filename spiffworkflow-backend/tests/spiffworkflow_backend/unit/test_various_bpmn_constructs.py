from uuid import UUID

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestVariousBpmnConstructs(BaseTest):
    def test_running_process_with_timer_intermediate_catch_event(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/timer_intermediate_catch_event",
            process_model_source_directory="timer_intermediate_catch_event",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

    # the bug here was that we were failing to persist the multi-instance task to the db.
    # normally, we persist all waiting tasks to the db, but for human tasks, we follow a different code path.
    # To fix it, we detect that we are a child of a multi-instance task, and make sure we add our parent (the multi-instance task)
    # to the list of tasks to persist. This way, the list of children on the multi-instance task is updated correctly.
    def test_multi_instances_user_task_with_celery(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True):
            process_model = load_test_spec(
                process_model_id="group/multiinstance_user_task_sequential",
                process_model_source_directory="multiinstance_user_task_sequential",
            )
            process_instance = self.create_process_instance_from_process_model(process_model=process_model)
            processor = ProcessInstanceProcessor(process_instance)
            processor.do_engine_steps(save=True)

            process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
            processor = ProcessInstanceProcessor(process_instance)
            human_task_one = process_instance.active_human_tasks[0]
            spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
            assert len(spiff_manual_task.parent.children) == 2
            ProcessInstanceService.complete_form_task(
                processor=processor,
                spiff_task=spiff_manual_task,
                data={"val": "1"},
                user=process_instance.process_initiator,
                human_task=human_task_one,
                execution_mode="asynchronous",
            )
            assert len(spiff_manual_task.parent.children) == 3

            process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
            processor = ProcessInstanceProcessor(process_instance)
            human_task_one = process_instance.active_human_tasks[0]
            spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
            assert len(spiff_manual_task.parent.children) == 3
            ProcessInstanceService.complete_form_task(
                processor=processor,
                spiff_task=spiff_manual_task,
                data={"val": "2"},
                user=process_instance.process_initiator,
                human_task=human_task_one,
            )
            assert len(spiff_manual_task.parent.children) == 4

            process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
            processor = ProcessInstanceProcessor(process_instance)
            human_task_one = process_instance.active_human_tasks[0]
            spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
            assert len(spiff_manual_task.parent.children) == 4
            ProcessInstanceService.complete_form_task(
                processor=processor,
                spiff_task=spiff_manual_task,
                data={"val": "3"},
                user=process_instance.process_initiator,
                human_task=human_task_one,
            )
            assert len(spiff_manual_task.parent.children) == 4

            processor.do_engine_steps(save=True)
            assert process_instance.status == "complete"

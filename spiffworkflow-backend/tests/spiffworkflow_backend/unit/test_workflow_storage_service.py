from flask.app import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.workflow_storage_service import WorkflowStorageService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestWorkflowStorageService(BaseTest):
    def test_strategy_resolution_prefers_process_instance_override(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        app.config["SPIFFWORKFLOW_BACKEND_WORKFLOW_STORAGE_STRATEGY"] = WorkflowStorageService.TASK_BASED

        process_instance = ProcessInstanceModel(
            status=ProcessInstanceStatus.not_started.value,
            process_initiator_id=with_super_admin_user.id,
            process_model_identifier="test_group/simple_form",
            process_model_display_name="simple_form",
            start_in_seconds=0,
            workflow_storage_strategy=WorkflowStorageService.BLOB_BASED,
        )
        db.session.add(process_instance)
        db.session.commit()

        assert WorkflowStorageService.strategy_for_process_instance(process_instance) == WorkflowStorageService.BLOB_BASED

    def test_workflow_blob_round_trip(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_instance = ProcessInstanceModel(
            status=ProcessInstanceStatus.not_started.value,
            process_initiator_id=with_super_admin_user.id,
            process_model_identifier="test_group/simple_form",
            process_model_display_name="simple_form",
            start_in_seconds=0,
            workflow_storage_strategy=WorkflowStorageService.BLOB_BASED,
        )
        db.session.add(process_instance)
        db.session.commit()

        expected = {"serializer_version": "1.0", "tasks": {}}
        WorkflowStorageService.save_workflow(process_instance, expected)
        db.session.commit()

        loaded = WorkflowStorageService.load_workflow(process_instance)
        assert loaded == expected

    def test_blob_get_task_uses_subprocess_bpmn_process(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = load_test_spec(
            "test_group/data-object-in-subprocess",
            process_model_source_directory="data-object-in-subprocess",
        )
        process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
        processor = ProcessInstanceProcessor(
            process_instance,
            include_task_data_for_completed_tasks=True,
            include_completed_subprocesses=True,
        )
        processor.do_engine_steps(save=True)
        WorkflowStorageService.save_workflow(process_instance, processor.serialize())
        process_instance.workflow_storage_strategy = WorkflowStorageService.BLOB_BASED
        db.session.add(process_instance)
        db.session.commit()

        task_rows = WorkflowStorageService.list_tasks(process_instance)
        subprocess_task = next(task for task in task_rows if task["bpmn_process_guid"] is not None)
        synthetic_task = WorkflowStorageService.get_task(task_guid=subprocess_task["guid"], process_instance=process_instance)

        assert synthetic_task.bpmn_process is not None
        assert synthetic_task.bpmn_process.guid == subprocess_task["bpmn_process_guid"]

    def test_parent_subprocess_task_guids_for_task_returns_parent_chain(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model = load_test_spec(
            "test_group/data-object-in-subprocess",
            process_model_source_directory="data-object-in-subprocess",
        )
        process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
        processor = ProcessInstanceProcessor(
            process_instance,
            include_task_data_for_completed_tasks=True,
            include_completed_subprocesses=True,
        )
        processor.do_engine_steps(save=True)
        WorkflowStorageService.save_workflow(process_instance, processor.serialize())
        process_instance.workflow_storage_strategy = WorkflowStorageService.BLOB_BASED
        db.session.add(process_instance)
        db.session.commit()

        task_rows = WorkflowStorageService.list_tasks(process_instance)
        subprocess_task = next(task for task in task_rows if task["bpmn_process_guid"] is not None)
        parent_guids = WorkflowStorageService.parent_subprocess_task_guids_for_task(
            task_guid=subprocess_task["guid"], process_instance=process_instance
        )

        assert len(parent_guids) > 0
        assert parent_guids[0] == subprocess_task["bpmn_process_guid"]

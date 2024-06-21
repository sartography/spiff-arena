import copy
import json
import os

from flask.app import Flask
from flask.testing import FlaskClient
from SpiffWorkflow.bpmn.serializer.migration.version_1_3 import update_data_objects  # type: ignore
from spiffworkflow_backend.constants import SPIFFWORKFLOW_BACKEND_DATA_MIGRATION_CHECKSUM
from spiffworkflow_backend.constants import SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.data_migrations.version_1_3 import VersionOneThree
from spiffworkflow_backend.data_migrations.version_4 import Version4
from spiffworkflow_backend.data_migrations.version_5 import Version5
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from sqlalchemy import or_

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstanceMigrator(BaseTest):
    def test_data_migrations_directory_has_not_changed(
        self,
        app: Flask,
        client: FlaskClient,
    ) -> None:
        md5checksums = ProcessInstanceMigrator.generate_migration_checksum()
        assert md5checksums == SPIFFWORKFLOW_BACKEND_DATA_MIGRATION_CHECKSUM, (
            "Data migrations seem to have changed but checksum has not been updated. "
            "Please update SPIFFWORKFLOW_BACKEND_DATA_MIGRATION_CHECKSUM"
        )

        highest_version = 0
        for file in ProcessInstanceMigrator.get_migration_files():
            current_version = os.path.basename(file).replace("version_", "").replace(".py", "").replace("_", ".")
            if current_version == "1.3":
                continue
            if int(current_version) > highest_version:
                highest_version = int(current_version)
        assert highest_version == int(SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION), (
            f"Highest migration version file is '{highest_version}' however "
            f"SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION is '{SPIFFWORKFLOW_BACKEND_SERIALIZER_VERSION}'"
        )

    def test_can_run_all_migrations(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        process_instance.spiff_serializer_version = "1"
        db.session.add(process_instance)
        db.session.commit()

        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        ProcessInstanceMigrator.run(process_instance)

    def test_can_run_version_1_3_migration(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        process_instance.spiff_serializer_version = "1"
        db.session.add(process_instance)
        db.session.commit()
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        task_model = (
            TaskModel.query.filter_by(process_instance_id=process_instance.id)
            .join(TaskDefinitionModel)
            .filter(TaskDefinitionModel.bpmn_identifier == "finance_approval")
            .first()
        )
        assert task_model is not None
        assert task_model.parent_task_model() is not None
        assert task_model.parent_task_model().properties_json["last_state_change"] is not None

        new_properties_json = copy.copy(task_model.properties_json)
        new_properties_json["last_state_change"] = None
        task_model.properties_json = new_properties_json
        db.session.add(task_model)
        db.session.commit()
        task_model = TaskModel.query.filter_by(guid=task_model.guid).first()
        assert task_model.properties_json["last_state_change"] is None

        VersionOneThree().run()
        task_model = TaskModel.query.filter_by(guid=task_model.guid).first()
        assert task_model.properties_json["last_state_change"] is not None

    def test_can_run_version_4_migration(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/service-task-with-data-obj",
            process_model_source_directory="service-task-with-data-obj",
        )
        (process_instance, bpmn_process_dict_version_4_from_spiff) = self._import_bpmn_json_for_test(
            app, "bpmn_process_instance_data_objects_version_3.json", process_model
        )
        bpmn_process_cache_version_3 = {
            "bpmn_process_definition_id": process_instance.bpmn_process_definition_id,
            "bpmn_process_id": process_instance.bpmn_process_id,
        }

        process_instance_events = ProcessInstanceEventModel.query.filter_by(process_instance_id=process_instance.id).all()
        pi_events_count_before = len(process_instance_events)
        Version4.run(process_instance)
        update_data_objects(bpmn_process_dict_version_4_from_spiff)
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(
            process_instance, include_task_data_for_completed_tasks=True, include_completed_subprocesses=True
        )
        bpmn_process_dict_version_4 = processor.serialize(serialize_script_engine_state=False)
        self.round_last_state_change(bpmn_process_dict_version_4)
        self.round_last_state_change(bpmn_process_dict_version_4_from_spiff)
        assert bpmn_process_dict_version_4 == bpmn_process_dict_version_4_from_spiff

        bpmn_process_cache_version_4 = {
            "bpmn_process_definition_id": process_instance.bpmn_process_definition_id,
            "bpmn_process_id": process_instance.bpmn_process_id,
        }
        assert (
            bpmn_process_cache_version_4["bpmn_process_definition_id"]
            != bpmn_process_cache_version_3["bpmn_process_definition_id"]
        )
        assert bpmn_process_cache_version_4["bpmn_process_id"] == bpmn_process_cache_version_3["bpmn_process_id"]
        assert (
            process_instance.bpmn_process.bpmn_process_definition_id == bpmn_process_cache_version_4["bpmn_process_definition_id"]
        )

        bpmn_processes = BpmnProcessModel.query.filter(
            or_(
                BpmnProcessModel.id == process_instance.bpmn_process_id,
                BpmnProcessModel.top_level_process_id == process_instance.bpmn_process_id,
            )
        ).all()
        assert len(bpmn_processes) == 3

        for bpmn_process in bpmn_processes:
            for task_model in bpmn_process.tasks:
                assert task_model.task_definition.bpmn_process_definition_id == bpmn_process.bpmn_process_definition_id

        process_instance_events = ProcessInstanceEventModel.query.filter_by(process_instance_id=process_instance.id).all()
        pi_events_count_after = len(process_instance_events)
        assert pi_events_count_before == pi_events_count_after

    def test_can_run_version_5_migration(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/multiinstance_manual_task",
            process_model_source_directory="multiinstance_manual_task",
        )
        (process_instance, _bpmn_process_dict_before_import) = self._import_bpmn_json_for_test(
            app, "bpmn_multi_instance_task_version_4.json", process_model
        )
        tasks = (
            TaskModel.query.filter_by(process_instance_id=process_instance.id)
            .join(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
            .filter(TaskDefinitionModel.bpmn_identifier == "manual_task")
            .all()
        )
        assert len(tasks) == 1
        assert tasks[0].state == "WAITING"
        Version5.run(process_instance)
        db.session.commit()
        tasks = (
            TaskModel.query.filter_by(process_instance_id=process_instance.id)
            .join(TaskDefinitionModel, TaskDefinitionModel.id == TaskModel.task_definition_id)
            .filter(TaskDefinitionModel.bpmn_identifier == "manual_task")
            .all()
        )
        assert len(tasks) == 1
        assert tasks[0].state == "STARTED"

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        # save the processor so it creates the human tasks
        processor.save()
        self.complete_next_manual_task(processor, execution_mode="synchronous")
        self.complete_next_manual_task(processor, execution_mode="synchronous")
        assert process_instance.status == ProcessInstanceStatus.complete.value

    def _import_bpmn_json_for_test(self, app: Flask, bpmn_json_file_name: str, process_model: ProcessModelInfo) -> tuple:
        bpmn_json_file = os.path.join(
            app.instance_path,
            "..",
            "..",
            "tests",
            "files",
            bpmn_json_file_name,
        )
        with open(bpmn_json_file) as f:
            bpmn_process_dict_before_import = json.loads(f.read())
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        ProcessInstanceProcessor.persist_bpmn_process_dict(
            bpmn_process_dict_before_import,
            process_instance_model=process_instance,
            bpmn_definition_to_task_definitions_mappings={},
        )
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()

        # ensure data was imported correctly and is in expected state
        processor = ProcessInstanceProcessor(
            process_instance, include_task_data_for_completed_tasks=True, include_completed_subprocesses=True
        )
        bpmn_process_dict_version_3_after_import = processor.serialize(serialize_script_engine_state=False)
        self.round_last_state_change(bpmn_process_dict_before_import)
        self.round_last_state_change(bpmn_process_dict_version_3_after_import)
        assert bpmn_process_dict_version_3_after_import == bpmn_process_dict_before_import
        return (process_instance, bpmn_process_dict_before_import)

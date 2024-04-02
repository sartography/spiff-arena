import copy

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
from spiffworkflow_backend.data_migrations.version_1_3 import VersionOneThree
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstanceMigrator(BaseTest):
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

    # def test_can_run_version_4_migration(
    #     self,
    #     app: Flask,
    #     client: FlaskClient,
    #     with_db_and_bpmn_file_cleanup: None,
    # ) -> None:
    #     version_3_json = os.path.join(
    #         app.instance_path,
    #         "..",
    #         "..",
    #         "tests",
    #         "files",
    #         "bpmn_process_instance_data_objects_version_3.json",
    #     )
    #     with open(version_3_json) as f:
    #         bpmn_process_dict_version_3 = json.loads(f.read())
    #     bpmn_process_dict_version_4_from_spiff = copy.deepcopy(bpmn_process_dict_version_3)
    #     process_model = load_test_spec(
    #         process_model_id="test_group/service-task-with-data-obj",
    #         process_model_source_directory="service-task-with-data-obj",
    #     )
    #     process_instance = self.create_process_instance_from_process_model(process_model=process_model)
    #     ProcessInstanceProcessor.persist_bpmn_process_dict(
    #         bpmn_process_dict_version_3, process_instance_model=process_instance, bpmn_definition_to_task_definitions_mappings={}
    #     )
    #     process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
    #
    #     # ensure data was imported correctly and is in expected state
    #     processor = ProcessInstanceProcessor(process_instance)
    #     bpmn_process_dict_version_3_after_import = processor.serialize()
    #     self.round_last_state_change(bpmn_process_dict_version_3)
    #     self.round_last_state_change(bpmn_process_dict_version_3_after_import)
    #     assert bpmn_process_dict_version_3_after_import == bpmn_process_dict_version_3
    #     bpmn_process_cache_version_3 = {
    #         "bpmn_process_definition_id": process_instance.bpmn_process_definition_id,
    #         "bpmn_process_id": process_instance.bpmn_process_id,
    #     }
    #
    #     process_instance_events = ProcessInstanceEventModel.query.filter_by(process_instance_id=process_instance.id).all()
    #     pi_events_count_before = len(process_instance_events)
    #     Version4.run(process_instance)
    #     update_data_objects(bpmn_process_dict_version_4_from_spiff)
    #     process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
    #     processor = ProcessInstanceProcessor(process_instance)
    #     bpmn_process_dict_version_4 = processor.serialize()
    #     self.round_last_state_change(bpmn_process_dict_version_4)
    #     self.round_last_state_change(bpmn_process_dict_version_4_from_spiff)
    #     assert bpmn_process_dict_version_4 == bpmn_process_dict_version_4_from_spiff
    #
    #     bpmn_process_cache_version_4 = {
    #         "bpmn_process_definition_id": process_instance.bpmn_process_definition_id,
    #         "bpmn_process_id": process_instance.bpmn_process_id,
    #     }
    #     assert (
    #         bpmn_process_cache_version_4["bpmn_process_definition_id"]
    #         != bpmn_process_cache_version_3["bpmn_process_definition_id"]
    #     )
    #     assert bpmn_process_cache_version_4["bpmn_process_id"] == bpmn_process_cache_version_3["bpmn_process_id"]
    #     assert (
    #         process_instance.bpmn_process.bpmn_process_definition_id == bpmn_process_cache_version_4["bpmn_process_definition_id"]
    #     )
    #
    #     bpmn_processes = BpmnProcessModel.query.filter(
    #         or_(
    #             BpmnProcessModel.id == process_instance.bpmn_process_id,
    #             BpmnProcessModel.top_level_process_id == process_instance.bpmn_process_id,
    #         )
    #     ).all()
    #     assert len(bpmn_processes) == 3
    #
    #     for bpmn_process in bpmn_processes:
    #         for task_model in bpmn_process.tasks:
    #             assert task_model.task_definition.bpmn_process_definition_id == bpmn_process.bpmn_process_definition_id
    #
    #     process_instance_events = ProcessInstanceEventModel.query.filter_by(process_instance_id=process_instance.id).all()
    #     pi_events_count_after = len(process_instance_events)
    #     assert pi_events_count_before == pi_events_count_after

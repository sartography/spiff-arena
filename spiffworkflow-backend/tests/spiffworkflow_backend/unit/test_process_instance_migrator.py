from spiffworkflow_backend.data_migrations.process_instance_migrator import ProcessInstanceMigrator
import copy
from spiffworkflow_backend.models.task import TaskModel # noqa: F401
from spiffworkflow_backend.data_migrations.version_1_3 import VersionOneThree
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec
from spiffworkflow_backend.models.db import db
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from spiffworkflow_backend.models.user import UserModel
from flask.testing import FlaskClient
from flask.app import Flask

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
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model
        )
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
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model
        )
        process_instance.spiff_serializer_version = "1"
        db.session.add(process_instance)
        db.session.commit()
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        task_model = TaskModel.query.filter_by(process_instance_id=process_instance.id).all()[-1]
        assert task_model is not None
        assert task_model.parent_task_model() is not None
        assert task_model.parent_task_model().properties_json['last_state_change'] is not None

        new_properties_json = copy.copy(task_model.properties_json)
        new_properties_json['last_state_change'] = None
        task_model.properties_json = new_properties_json
        db.session.add(task_model)
        db.session.commit()
        assert task_model.properties_json['last_state_change'] is None

        VersionOneThree().run()
        task_model = TaskModel.query.filter_by(id=task_model.id).first()
        assert task_model.properties_json['last_state_change'] is not None

import hashlib
import json

from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.data_migrations.process_instance_file_data_migrator import ProcessInstanceFileDataMigrator
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_file_data import PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_model_service import ProcessModelService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstanceFileDataMigrator(BaseTest):
    def test_can_migrate_from_db_to_fs(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/random_fact",
            bpmn_file_name="random_fact_set.bpmn",
            process_model_source_directory="random_fact",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == ProcessInstanceStatus.complete.value

        test_file_one_contents = json.dumps({"hello": "hey"})
        test_file_one_digest = hashlib.sha256(test_file_one_contents.encode()).hexdigest()
        pi_files = [
            {
                "mimetype": "application/json",
                "filename": "test_file_one.json",
                "contents": test_file_one_contents,
                "digest": test_file_one_digest,
            }
        ]
        for pi_file in pi_files:
            pi_model = ProcessInstanceFileDataModel(
                process_instance_id=process_instance.id,
                mimetype=pi_file["mimetype"],
                filename=pi_file["filename"],
                contents=pi_file["contents"].encode(),
                digest=pi_file["digest"],
            )
            db.session.add(pi_model)
        db.session.commit()

        with self.app_config_mock(
            app, "SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH", ProcessModelService.root_path()
        ):
            ProcessInstanceFileDataMigrator.migrate_from_database_to_filesystem()

            test_file_one_model = ProcessInstanceFileDataModel.query.filter_by(filename="test_file_one.json").first()
            assert test_file_one_model is not None
            assert test_file_one_model.contents == PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM.encode()
            assert test_file_one_model.get_contents() == test_file_one_contents.encode()

    def test_can_migrate_binary_file_from_db_to_fs(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/random_fact",
            bpmn_file_name="random_fact_set.bpmn",
            process_model_source_directory="random_fact",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert process_instance.status == ProcessInstanceStatus.complete.value

        # b'\xff\xfe\r\x00\n'
        test_file_one_contents = b"\xff\xfe\r\x00\n"
        test_file_one_digest = hashlib.sha256(test_file_one_contents).hexdigest()
        pi_files = [
            {
                "mimetype": "application/json",
                "filename": "test_file_one.json",
                "contents": test_file_one_contents,
                "digest": test_file_one_digest,
            }
        ]
        for pi_file in pi_files:
            pi_model = ProcessInstanceFileDataModel(
                process_instance_id=process_instance.id,
                mimetype=str(pi_file["mimetype"]),
                filename=str(pi_file["filename"]),
                contents=pi_file["contents"],  # type: ignore
                digest=str(pi_file["digest"]),
            )
            db.session.add(pi_model)
        db.session.commit()

        with self.app_config_mock(
            app, "SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH", ProcessModelService.root_path()
        ):
            ProcessInstanceFileDataMigrator.migrate_from_database_to_filesystem()

            test_file_one_model = ProcessInstanceFileDataModel.query.filter_by(filename="test_file_one.json").first()
            assert test_file_one_model is not None
            assert test_file_one_model.contents == PROCESS_INSTANCE_DATA_FILE_ON_FILE_SYSTEM.encode()
            assert test_file_one_model.get_contents() == test_file_one_contents

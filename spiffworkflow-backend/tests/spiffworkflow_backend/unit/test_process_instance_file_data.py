import hashlib

from flask.app import Flask
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessInstanceFileData(BaseTest):
    def test_returns_correct_dir_structure_from_digest(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        digest = hashlib.sha256(b"OH YEAH").hexdigest()
        digest_parts = ProcessInstanceFileDataModel.get_hashed_directory_structure(digest)
        assert digest == "b65b894bb56d8cf56e1045bbac80ea1d313640f7ee3ee724f43b2a07be5bff5f"
        assert digest_parts == ["b6", "5b"]

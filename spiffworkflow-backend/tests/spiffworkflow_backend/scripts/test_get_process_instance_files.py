import base64
import hashlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import pytest
from flask.app import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_process_instance_files import GetProcessInstanceFiles
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


def _data_url(mimetype: str, filename: str, contents: bytes) -> str:
    return f"data:{mimetype};name={filename};base64,{base64.b64encode(contents).decode('ascii')}"


@contextmanager
def _capture_queries() -> Iterator[list[str]]:
    statements: list[str] = []

    connection = db.session.connection()
    with patch.object(connection, "execute", wraps=connection.execute) as execute:
        yield statements
        statements.extend(str(call.args[0]) for call in execute.call_args_list)


class TestGetProcessInstanceFiles(BaseTest):
    @pytest.mark.parametrize("use_file_system", [False, True])
    def test_returns_all_files_for_only_the_current_process_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        tmp_path: Path,
        use_file_system: bool,
    ) -> None:
        if use_file_system:
            app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"] = str(tmp_path)
        try:
            process_model = load_test_spec(
                process_model_id="misc/category_number_one/simple_form",
                process_model_source_directory="simple_form",
            )
            process_instance = self.create_process_instance_from_process_model(process_model)
            other_process_instance = self.create_process_instance_from_process_model(process_model)

            # The second upload replaces the first in task data, like a resubmitted form.
            # The script must still return both.
            first_data = {"attachments": [_data_url("text/plain", "calc.txt", b"first version")]}
            second_data = {"attachments": [_data_url("text/plain", "calc%20final.txt", b"second version")]}
            ProcessInstanceService.save_file_data_and_replace_with_digest_references(first_data, process_instance.id)
            ProcessInstanceService.save_file_data_and_replace_with_digest_references(second_data, process_instance.id)
            ProcessInstanceService.save_file_data_and_replace_with_digest_references(
                {"f": _data_url("text/plain", "other.txt", b"other instance")}, other_process_instance.id
            )

            context = ScriptAttributesContext(
                task=None,
                environment_identifier="unit_testing",
                process_instance_id=process_instance.id,
                process_model_identifier=process_model.id,
            )
            db.session.expire_all()
            with _capture_queries() as queries:
                files = GetProcessInstanceFiles().run(context)
            assert len(queries) == 1
            assert "process_instance_file_data.contents" not in queries[0]
            assert [f["filename"] for f in files] == ["calc.txt", "calc final.txt"]
            assert files[0]["id"] < files[1]["id"]
            assert files[0]["digest"] == hashlib.sha256(b"first version").hexdigest()
            assert files[0]["mimetype"] == "text/plain"
            # file_reference matches what task data holds, so other scripts can take it.
            assert files[0]["file_reference"] == first_data["attachments"][0]
            assert files[1]["file_reference"] == second_data["attachments"][0]
            assert "data_url" not in files[0]

            db.session.expire_all()
            with _capture_queries() as queries:
                files_with_contents = GetProcessInstanceFiles().run(context, include_contents=True)
            assert len(queries) == 1
            assert "process_instance_file_data.contents" in queries[0]
            assert files_with_contents[0]["data_url"] == _data_url("text/plain", "calc.txt", b"first version")
            assert files_with_contents[1]["data_url"] == _data_url("text/plain", "calc%20final.txt", b"second version")
        finally:
            app.config["SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH"] = None

    def test_returns_empty_list_when_no_files(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="misc/category_number_one/simple_form",
            process_model_source_directory="simple_form",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        context = ScriptAttributesContext(
            task=None,
            environment_identifier="unit_testing",
            process_instance_id=process_instance.id,
            process_model_identifier=process_model.id,
        )
        assert GetProcessInstanceFiles().run(context) == []

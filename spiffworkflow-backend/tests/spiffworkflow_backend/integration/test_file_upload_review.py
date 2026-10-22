import base64
from hashlib import sha256
from pathlib import Path
from urllib.parse import quote

import pytest
from flask import Flask
from starlette.testclient import TestClient
from werkzeug.http import parse_options_header

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.tasks_controller import _dequeued_interstitial_stream
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

# Exercise all byte values, including NUL and non-UTF-8.
CONTENTS = bytes(range(256)) * 16


class TestFileUploadReview(BaseTest):
    @pytest.mark.parametrize("filesystem", [False, True])
    @pytest.mark.parametrize(
        ("mimetype", "filename"),
        [
            ("image/png", "image.png"),
            ("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "sheet.xlsx"),
            ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "document.docx"),
            ("application/vnd.openxmlformats-officedocument.wordprocessingml.document", "Provisions [draft]; coût=2.docx"),
        ],
    )
    def test_upload_survives_followup_reviews(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        tmp_path: Path,
        filesystem: bool,
        mimetype: str,
        filename: str,
    ) -> None:
        contents = CONTENTS
        digest = sha256(contents).hexdigest()
        reference = f"data:{mimetype};name={quote(filename, safe='')};base64,spifffiledatadigest+{digest}"
        payload = f"data:{mimetype};name={quote(filename, safe='')};base64,{base64.b64encode(contents).decode()}"
        headers = self.logged_in_headers(with_super_admin_user)
        with self.app_config_mock(
            app, "SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_FILE_DATA_FILESYSTEM_PATH", str(tmp_path) if filesystem else None
        ):
            model, instance_id = self.create_and_run_process_instance(
                client,
                with_super_admin_user,
                process_group_id="upload-tests",
                process_model_id="review",
                bpmn_file_location="file_upload_review",
            )
            _dequeued_interstitial_stream(instance_id)
            instance = ProcessInstanceModel.query.filter_by(id=instance_id).first()
            assert instance is not None
            task_id = instance.active_human_tasks[0].task_id
            response = client.put(f"/v1.0/tasks/{instance_id}/{task_id}", headers=headers, json={"file": payload})
            assert response.status_code == 200, response.text
            _dequeued_interstitial_stream(instance_id)

            download_path = f"/v1.0/process-data-file-download/upload-tests:review/{instance_id}/{digest}"
            reviewer = self.create_user_with_permission("reviewer", target_uri=download_path, permission_names=["read"])
            outsider = self.find_or_create_user("outsider")
            for step in ("review_one", "review_two"):
                db.session.expire_all()
                task_id = instance.active_human_tasks[0].task_id
                response = client.get(f"/v1.0/tasks/{instance_id}/{task_id}?with_form_data=true", headers=headers)
                assert response.status_code == 200, response.text
                task = response.json()
                assert task["data"]["file"] == reference
                assert task["data"]["link"].endswith(f"({app.config['SPIFFWORKFLOW_BACKEND_URL']}{download_path})")

                for user in (with_super_admin_user, reviewer):
                    response = client.get(download_path, headers=self.logged_in_headers(user))
                    assert response.status_code == 200, response.text
                    assert response.content == contents
                    assert response.headers["content-type"] == mimetype
                    disposition, parameters = parse_options_header(response.headers["content-disposition"])
                    assert disposition == "attachment"
                    assert parameters["filename"] == filename
                response = client.get(download_path, headers=self.logged_in_headers(outsider))
                assert response.status_code == 403
                response = client.put(f"/v1.0/tasks/{instance_id}/{task_id}", headers=headers, json={"file": reference})
                assert response.status_code == 200, (step, response.text)
                _dequeued_interstitial_stream(instance_id)

            db.session.expire_all()
            assert instance.status == "complete"
            files = ProcessInstanceFileDataModel.query.filter_by(process_instance_id=instance_id).all()
            assert len(files) == 1  # Re-submitting a reference must not upload its digest as a new file.
            assert files[0].get_contents() == contents

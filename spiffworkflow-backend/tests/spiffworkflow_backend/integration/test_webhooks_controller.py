from hmac import HMAC
import base64
import io
import json
import os
import time
from hashlib import sha256
from typing import Any

import flask
import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from SpiffWorkflow.util.task import TaskState  # type: ignore
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel
from spiffworkflow_backend.models.process_instance_report import ReportMetadata
from spiffworkflow_backend.models.process_model import NotificationType
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_caller_service import ProcessCallerService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestWebhooksController(BaseTest):
    def test_webhook_runs_configured_process_model(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        load_test_spec(
            "test_group/simple_script",
            process_model_source_directory="simple_script",
        )

        request_data = json.dumps({"body": "THIS IS OUR REQEST"})
        secret = app.config["SPIFFWORKFLOW_BACKEND_GITHUB_WEBHOOK_SECRET"].encode()
        encoded_signature = HMAC(key=secret, msg=request_data.encode(), digestmod=sha256).hexdigest()

        response = client.post(
            "/v1.0/webhook",
            headers={"X-Hub-Signature-256": f"sha256={encoded_signature}", "Content-type": "application/json"},
            data=request_data,
        )
        assert response.status_code == 200

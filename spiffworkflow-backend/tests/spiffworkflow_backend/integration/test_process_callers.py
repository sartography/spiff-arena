import base64
import io
import json
import os
import time
from hashlib import sha256
from typing import Any
from unittest.mock import patch

import flask
import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from SpiffWorkflow.util.task import TaskState  # type: ignore
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
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


class TestProcessCallers(BaseTest):
    def test_references_after_process_model_create(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.get(
            "/v1.0/processes/callers/Level2",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        
        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 1
        

    def test_references_after_process_model_delete(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_group_and_model_with_bpmn(
            client=client,
            user=with_super_admin_user,
            process_group_id="test_group_two",
            process_model_id="call_activity_nested",
            bpmn_file_location="call_activity_nested",
        )

        response = client.delete(
            "/v1.0/process-models/test_group_two:call_activity_nested",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        
        assert response.status_code == 200

        response = client.get(
            "/v1.0/processes/callers/Level2",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        
        assert response.status_code == 200
        assert response.json is not None
        assert isinstance(response.json, list)
        assert len(response.json) == 0
        

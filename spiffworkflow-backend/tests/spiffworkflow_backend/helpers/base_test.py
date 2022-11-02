"""Base_test."""
import io
import json
import os
import time
from typing import Any
from typing import Dict
from typing import Optional

from flask import current_app
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec
from werkzeug.test import TestResponse  # type: ignore

from spiffworkflow_backend.models.permission_assignment import Permission
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_model import NotificationType
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.user_service import UserService

# from tests.spiffworkflow_backend.helpers.test_data import logged_in_headers


class BaseTest:
    """BaseTest."""

    @staticmethod
    def find_or_create_user(username: str = "test_user_1") -> UserModel:
        """Find_or_create_user."""
        user = UserModel.query.filter_by(username=username).first()
        if isinstance(user, UserModel):
            return user

        user = UserService.create_user("internal", username, username=username)
        if isinstance(user, UserModel):
            return user

        raise ApiError(
            error_code="create_user_error",
            message=f"Cannot find or create user: {username}",
        )

    @staticmethod
    def get_open_id_constants(app: Flask) -> tuple:
        """Get_open_id_constants."""
        open_id_server_url = app.config["OPEN_ID_SERVER_URL"]
        open_id_client_id = app.config["OPEN_ID_CLIENT_ID"]
        open_id_realm_name = app.config["OPEN_ID_REALM_NAME"]
        open_id_client_secret_key = app.config[
            "OPEN_ID_CLIENT_SECRET_KEY"
        ]  # noqa: S105

        return (
            open_id_server_url,
            open_id_client_id,
            open_id_realm_name,
            open_id_client_secret_key,
        )

    def create_process_instance(
        self,
        client: FlaskClient,
        test_process_group_id: str,
        test_process_model_id: str,
        headers: Dict[str, str],
    ) -> TestResponse:
        """Create_process_instance."""
        load_test_spec(test_process_model_id, process_group_id=test_process_group_id)
        response = client.post(
            f"/v1.0/process-models/{test_process_group_id}/{test_process_model_id}/process-instances",
            headers=headers,
        )
        assert response.status_code == 201
        return response

    def create_process_model_with_api(
        self,
        client: FlaskClient,
        process_group_id: Optional[str] = None,
        process_model_id: str = "make_cookies",
        process_model_display_name: str = "Cooooookies",
        process_model_description: str = "Om nom nom delicious cookies",
        fault_or_suspend_on_exception: str = NotificationType.suspend.value,
        exception_notification_addresses: Optional[list] = None,
        primary_process_id: Optional[str] = None,
        primary_file_name: Optional[str] = None,
        user: Optional[UserModel] = None,
    ) -> TestResponse:
        """Create_process_model."""
        process_model_service = ProcessModelService()

        # make sure we have a group
        if process_group_id is None:
            process_group_tmp = ProcessGroup(
                id="test_cat",
                display_name="Test Category",
                display_order=0,
                admin=False,
            )
            process_group = process_model_service.add_process_group(process_group_tmp)
        else:
            process_group = ProcessModelService().get_process_group(process_group_id)

        if exception_notification_addresses is None:
            exception_notification_addresses = []
        model = ProcessModelInfo(
            id=process_model_id,
            display_name=process_model_display_name,
            description=process_model_description,
            process_group_id=process_group.id,
            is_review=False,
            primary_process_id=primary_process_id,
            primary_file_name=primary_file_name,
            fault_or_suspend_on_exception=fault_or_suspend_on_exception,
            exception_notification_addresses=exception_notification_addresses,
        )
        if user is None:
            user = self.find_or_create_user()

        response = client.post(
            "/v1.0/process-models",
            content_type="application/json",
            data=json.dumps(ProcessModelInfoSchema().dump(model)),
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 201
        return response

    def create_spec_file(
        self,
        client: FlaskClient,
        process_group_id: str = "random_fact",
        process_model_id: str = "random_fact",
        process_model: Optional[ProcessModelInfo] = None,
        file_name: str = "random_fact.svg",
        file_data: bytes = b"abcdef",
        user: Optional[UserModel] = None,
    ) -> Any:
        """Test_create_spec_file."""
        if process_model is None:
            process_model = load_test_spec(
                process_model_id, process_group_id=process_group_id
            )
        data = {"file": (io.BytesIO(file_data), file_name)}
        if user is None:
            user = self.find_or_create_user()
        response = client.post(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 201
        assert response.get_data() is not None
        file = json.loads(response.get_data(as_text=True))
        # assert FileType.svg.value == file["type"]
        # assert "image/svg+xml" == file["content_type"]

        response = client.get(
            f"/v1.0/process-models/{process_model.process_group_id}/{process_model.id}/files/{file_name}",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200
        file2 = json.loads(response.get_data(as_text=True))
        assert file["file_contents"] == file2["file_contents"]
        return file

    def create_process_group(
        self,
        client: FlaskClient,
        user: Any,
        process_group_id: str,
        display_name: str = "",
    ) -> str:
        """Create_process_group."""
        process_group = ProcessGroup(
            id=process_group_id, display_name=display_name, display_order=0, admin=False
        )
        response = client.post(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group)),
        )
        assert response.status_code == 201
        assert response.json is not None
        assert response.json["id"] == process_group_id
        return process_group_id

    # @staticmethod
    # def get_public_access_token(username: str, password: str) -> dict:
    #     """Get_public_access_token."""
    #     public_access_token = AuthenticationService().get_public_access_token(
    #         username, password
    #     )
    #     return public_access_token

    def create_process_instance_from_process_model(
        self,
        process_model: ProcessModelInfo,
        status: Optional[str] = "not_started",
        user: Optional[UserModel] = None,
    ) -> ProcessInstanceModel:
        """Create_process_instance_from_process_model."""
        if user is None:
            user = self.find_or_create_user()

        current_time = round(time.time())
        process_instance = ProcessInstanceModel(
            status=status,
            process_initiator=user,
            process_model_identifier=process_model.id,
            process_group_identifier=process_model.process_group_id,
            updated_at_in_seconds=round(time.time()),
            start_in_seconds=current_time - (3600 * 1),
            end_in_seconds=current_time - (3600 * 1 - 20),
        )
        db.session.add(process_instance)
        db.session.commit()
        return process_instance

    @classmethod
    def create_user_with_permission(
        cls,
        username: str,
        target_uri: str = PermissionTargetModel.URI_ALL,
        permission_names: Optional[list[str]] = None,
    ) -> UserModel:
        """Create_user_with_permission."""
        user = BaseTest.find_or_create_user(username=username)
        return cls.add_permissions_to_user(
            user, target_uri=target_uri, permission_names=permission_names
        )

    @classmethod
    def add_permissions_to_user(
        cls,
        user: UserModel,
        target_uri: str = PermissionTargetModel.URI_ALL,
        permission_names: Optional[list[str]] = None,
    ) -> UserModel:
        """Add_permissions_to_user."""
        permission_target = PermissionTargetModel.query.filter_by(
            uri=target_uri
        ).first()
        if permission_target is None:
            permission_target = PermissionTargetModel(uri=target_uri)
            db.session.add(permission_target)
            db.session.commit()

        if permission_names is None:
            permission_names = [member.name for member in Permission]

        for permission in permission_names:
            AuthorizationService.create_permission_for_principal(
                principal=user.principal,
                permission_target=permission_target,
                permission=permission,
            )
        return user

    @staticmethod
    def logged_in_headers(
        user: UserModel, _redirect_url: str = "http://some/frontend/url"
    ) -> Dict[str, str]:
        """Logged_in_headers."""
        return dict(Authorization="Bearer " + user.encode_auth_token())

    def get_test_data_file_contents(
        self, file_name: str, process_model_test_data_dir: str
    ) -> bytes:
        """Get_test_data_file_contents."""
        file_full_path = os.path.join(
            current_app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            process_model_test_data_dir,
            file_name,
        )
        with open(file_full_path, "rb") as file:
            return file.read()

    def assert_user_has_permission(
        self,
        user: UserModel,
        permission: str,
        target_uri: str,
        expected_result: bool = True,
    ) -> None:
        """Assert_user_has_permission."""
        has_permission = AuthorizationService.user_has_permission(
            user=user,
            permission=permission,
            target_uri=target_uri,
        )
        assert has_permission is expected_result

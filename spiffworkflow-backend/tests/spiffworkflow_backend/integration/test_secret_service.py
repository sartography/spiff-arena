"""Test_secret_service."""
import json
from typing import Optional

import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from flask_bpmn.api.api_error import ApiError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from werkzeug.test import TestResponse  # type: ignore

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.secret_model import SecretModel
from spiffworkflow_backend.models.secret_model import SecretModelSchema
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.secret_service import SecretService


class SecretServiceTestHelpers(BaseTest):
    """SecretServiceTestHelpers."""

    test_key = "test_key"
    test_value = "test_value"
    test_process_group_id = "test"
    test_process_group_display_name = "My Test Process Group"
    test_process_model_id = "make_cookies"
    test_process_model_display_name = "Cooooookies"
    test_process_model_description = "Om nom nom delicious cookies"

    def add_test_secret(self, user: UserModel) -> SecretModel:
        """Add_test_secret."""
        return SecretService().add_secret(self.test_key, self.test_value, user.id)

    def add_test_process(
        self, client: FlaskClient, user: UserModel
    ) -> ProcessModelInfo:
        """Add_test_process."""
        self.create_process_group(
            client,
            user,
            self.test_process_group_id,
            display_name=self.test_process_group_display_name,
        )
        process_model_identifier = (
            f"{self.test_process_group_id}/{self.test_process_model_id}"
        )
        self.create_process_model_with_api(
            client,
            process_model_id=process_model_identifier,
            process_model_display_name=self.test_process_model_display_name,
            process_model_description=self.test_process_model_description,
            user=user,
        )
        process_model_info = ProcessModelService.get_process_model(
            process_model_identifier
        )
        return process_model_info


class TestSecretService(SecretServiceTestHelpers):
    """TestSecretService."""

    def test_add_secret(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_add_secret."""
        test_secret = self.add_test_secret(with_super_admin_user)

        assert test_secret is not None
        assert test_secret.key == self.test_key
        assert test_secret.value == self.test_value
        assert test_secret.user_id == with_super_admin_user.id

    def test_add_secret_duplicate_key_fails(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_add_secret_duplicate_key_fails."""
        self.add_test_secret(with_super_admin_user)
        with pytest.raises(ApiError) as ae:
            self.add_test_secret(with_super_admin_user)
        assert ae.value.error_code == "create_secret_error"

    def test_get_secret(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_secret."""
        self.add_test_secret(with_super_admin_user)

        secret = SecretService().get_secret(self.test_key)
        assert secret is not None
        assert secret.value == self.test_value

    def test_get_secret_bad_key_fails(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_get_secret_bad_service."""
        self.add_test_secret(with_super_admin_user)

        with pytest.raises(ApiError):
            SecretService().get_secret("bad_key")

    def test_update_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test update secret."""
        self.add_test_secret(with_super_admin_user)
        secret = SecretService.get_secret(self.test_key)
        assert secret
        assert secret.value == self.test_value
        SecretService.update_secret(
            self.test_key, "new_secret_value", with_super_admin_user.id
        )
        new_secret = SecretService.get_secret(self.test_key)
        assert new_secret
        assert new_secret.value == "new_secret_value"  # noqa: S105

    def test_update_secret_bad_secret_fails(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_update_secret_bad_secret_fails."""
        secret = self.add_test_secret(with_super_admin_user)
        with pytest.raises(ApiError) as ae:
            SecretService.update_secret(
                secret.key + "x", "some_new_value", with_super_admin_user.id
            )
        assert "Resource does not exist" in ae.value.message
        assert ae.value.error_code == "update_secret_error"

    def test_delete_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test delete secret."""
        self.add_test_secret(with_super_admin_user)
        secrets = SecretModel.query.all()
        assert len(secrets) == 1
        assert secrets[0].user_id == with_super_admin_user.id
        SecretService.delete_secret(self.test_key, with_super_admin_user.id)
        secrets = SecretModel.query.all()
        assert len(secrets) == 0

    def test_delete_secret_bad_secret_fails(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_delete_secret_bad_secret_fails."""
        self.add_test_secret(with_super_admin_user)
        with pytest.raises(ApiError) as ae:
            SecretService.delete_secret(self.test_key + "x", with_super_admin_user.id)
        assert "Resource does not exist" in ae.value.message


class TestSecretServiceApi(SecretServiceTestHelpers):
    """TestSecretServiceApi."""

    def test_add_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_add_secret."""
        secret_model = SecretModel(
            key=self.test_key,
            value=self.test_value,
            user_id=with_super_admin_user.id,
        )
        data = json.dumps(SecretModelSchema().dump(secret_model))
        response: TestResponse = client.post(
            "/v1.0/secrets",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=data,
        )
        assert response.json
        secret: dict = response.json
        for key in ["key", "value", "user_id"]:
            assert key in secret.keys()
        assert secret["key"] == self.test_key
        assert secret["value"] == self.test_value
        assert secret["user_id"] == with_super_admin_user.id

    def test_get_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test get secret."""
        self.add_test_secret(with_super_admin_user)
        secret_response = client.get(
            f"/v1.0/secrets/{self.test_key}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert secret_response
        assert secret_response.status_code == 200
        assert secret_response.json
        assert secret_response.json["value"] == self.test_value

    def test_update_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_update_secret."""
        self.add_test_secret(with_super_admin_user)
        secret: Optional[SecretModel] = SecretService.get_secret(self.test_key)
        assert secret
        assert secret.value == self.test_value
        secret_model = SecretModel(
            key=self.test_key,
            value="new_secret_value",
            user_id=with_super_admin_user.id,
        )
        response = client.put(
            f"/v1.0/secrets/{self.test_key}",
            headers=self.logged_in_headers(with_super_admin_user),
            content_type="application/json",
            data=json.dumps(SecretModelSchema().dump(secret_model)),
        )
        assert response.status_code == 200

        secret_model = SecretModel.query.filter(
            SecretModel.key == self.test_key
        ).first()
        assert secret_model.value == "new_secret_value"

    def test_delete_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test delete secret."""
        self.add_test_secret(with_super_admin_user)
        secret = SecretService.get_secret(self.test_key)
        assert secret
        assert secret.value == self.test_value
        secret_response = client.delete(
            f"/v1.0/secrets/{self.test_key}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert secret_response.status_code == 200
        with pytest.raises(ApiError):
            secret = SecretService.get_secret(self.test_key)

    def test_delete_secret_bad_key(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test delete secret."""
        secret_response = client.delete(
            "/v1.0/secrets/bad_secret_key",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert secret_response.status_code == 404

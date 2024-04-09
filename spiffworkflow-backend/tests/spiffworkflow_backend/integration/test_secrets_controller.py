import json

import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.secret_model import SecretModel
from spiffworkflow_backend.models.secret_model import SecretModelSchema
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.secret_service import SecretService

from tests.spiffworkflow_backend.integration.test_secret_service import SecretServiceTestHelpers


class TestSecretsController(SecretServiceTestHelpers):
    def test_add_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        secret_model = SecretModel(
            key=self.test_key,
            value=self.test_value,
            user_id=with_super_admin_user.id,
        )
        data = json.dumps(SecretModelSchema().dump(secret_model))
        response = client.post(
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
        assert SecretService._decrypt(secret["value"]) == self.test_value
        assert secret["user_id"] == with_super_admin_user.id

    def test_get_secret_api(
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
        assert "value" not in secret_response.json

    def test_get_secret_value(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test get secret."""
        self.add_test_secret(with_super_admin_user)
        secret_response = client.get(
            f"/v1.0/secrets/show-value/{self.test_key}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert secret_response
        assert secret_response.status_code == 200
        assert secret_response.json
        assert SecretService._decrypt(secret_response.json["value"]) == self.test_value

    def test_update_secret(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.add_test_secret(with_super_admin_user)
        secret: SecretModel | None = SecretService.get_secret(self.test_key)
        assert secret
        assert SecretService._decrypt(secret.value) == self.test_value
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

        secret_model = SecretModel.query.filter(SecretModel.key == self.test_key).first()
        assert SecretService._decrypt(secret_model.value) == "new_secret_value"

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
        assert SecretService._decrypt(secret.value) == self.test_value
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

    def test_secret_list(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.add_test_secret(with_super_admin_user)
        secret_response = client.get(
            "/v1.0/secrets",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert secret_response.status_code == 200
        first_secret_in_results = secret_response.json["results"][0]
        assert first_secret_in_results["key"] == self.test_key
        assert "value" not in first_secret_in_results

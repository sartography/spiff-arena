import pytest
from flask.app import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.secret_model import SecretModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.secret_service import SecretService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class SecretServiceTestHelpers(BaseTest):
    test_key = "test_key"
    test_value = "test_value"
    test_process_group_id = "test"
    test_process_group_display_name = "My Test Process Group"
    test_process_model_id = "make_cookies"
    test_process_model_display_name = "Cooooookies"
    test_process_model_description = "Om nom nom delicious cookies"

    def add_test_secret(self, user: UserModel) -> SecretModel:
        return SecretService().add_secret(self.test_key, self.test_value, user.id)

    def add_test_process(self, client: FlaskClient, user: UserModel) -> ProcessModelInfo:
        self.create_process_group_with_api(
            client,
            user,
            self.test_process_group_id,
            display_name=self.test_process_group_display_name,
        )
        process_model_identifier = f"{self.test_process_group_id}/{self.test_process_model_id}"
        self.create_process_model_with_api(
            client,
            process_model_id=process_model_identifier,
            process_model_display_name=self.test_process_model_display_name,
            process_model_description=self.test_process_model_description,
            user=user,
        )
        process_model_info = ProcessModelService.get_process_model(process_model_identifier)
        return process_model_info


class TestSecretService(SecretServiceTestHelpers):
    def test_add_secret(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        test_secret = self.add_test_secret(with_super_admin_user)

        assert test_secret is not None
        assert test_secret.key == self.test_key
        assert SecretService._decrypt(test_secret.value) == self.test_value
        assert test_secret.user_id == with_super_admin_user.id

    def test_add_secret_duplicate_key_fails(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
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
        self.add_test_secret(with_super_admin_user)

        secret = SecretService().get_secret(self.test_key)
        assert secret is not None
        assert SecretService._decrypt(secret.value) == self.test_value

    def test_get_secret_bad_key_fails(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
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
        assert SecretService._decrypt(secret.value) == self.test_value
        SecretService.update_secret(self.test_key, "new_secret_value", with_super_admin_user.id)
        new_secret = SecretService.get_secret(self.test_key)
        assert new_secret
        assert SecretService._decrypt(new_secret.value) == "new_secret_value"  # noqa: S105

    def test_update_secret_bad_secret_fails(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        secret = self.add_test_secret(with_super_admin_user)
        with pytest.raises(ApiError) as ae:
            SecretService.update_secret(secret.key + "x", "some_new_value", with_super_admin_user.id)
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
        self.add_test_secret(with_super_admin_user)
        with pytest.raises(ApiError) as ae:
            SecretService.delete_secret(self.test_key + "x", with_super_admin_user.id)
        assert "Resource does not exist" in ae.value.message

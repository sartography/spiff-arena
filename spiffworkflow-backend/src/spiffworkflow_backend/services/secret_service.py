"""Secret_service."""
from typing import Optional

from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db

from spiffworkflow_backend.models.secret_model import SecretModel

# from cryptography.fernet import Fernet
#
#
# class EncryptionService:
#     key = Fernet.generate_key()  # this is your "password"
#     cipher_suite = Fernet(key)
#     encoded_text = cipher_suite.encrypt(b"Hello stackoverflow!")
#     decoded_text = cipher_suite.decrypt(encoded_text)


class SecretService:
    """SecretService."""

    # def encrypt_key(self, plain_key: str) -> str:
    #     """Encrypt_key."""
    #     # flask_secret = current_app.secret_key
    #     # print("encrypt_key")
    #     ...

    # def decrypt_key(self, encrypted_key: str) -> str:
    #     """Decrypt key."""
    #     ...

    @staticmethod
    def add_secret(
        key: str,
        value: str,
        user_id: int,
    ) -> SecretModel:
        """Add_secret."""
        # encrypted_key = self.encrypt_key(key)
        secret_model = SecretModel(key=key, value=value, user_id=user_id)
        db.session.add(secret_model)
        try:
            db.session.commit()
        except Exception as e:
            raise ApiError(
                error_code="create_secret_error",
                message=f"There was an error creating a secret with key: {key} and value ending with: {value[:-4]}. "
                f"Original error is {e}",
            ) from e
        return secret_model

    @staticmethod
    def get_secret(key: str) -> SecretModel:
        """Get_secret."""
        secret = db.session.query(SecretModel).filter(SecretModel.key == key).first()
        if isinstance(secret, SecretModel):
            return secret
        else:
            raise ApiError(
                error_code="missing_secret_error",
                message=f"Unable to locate a secret with the name: {key}. ",
            )

    @staticmethod
    def update_secret(
        key: str,
        value: str,
        user_id: int,
        create_if_not_exists: Optional[bool] = False,
    ) -> None:
        """Does this pass pre commit?"""
        secret_model = SecretModel.query.filter(SecretModel.key == key).first()
        if secret_model:
            secret_model.value = value
            db.session.add(secret_model)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e
        elif create_if_not_exists:
            SecretService.add_secret(key=key, value=value, user_id=user_id)
        else:
            raise ApiError(
                error_code="update_secret_error",
                message=f"Cannot update secret with key: {key}. Resource does not exist.",
                status_code=404,
            )

    @staticmethod
    def delete_secret(key: str, user_id: int) -> None:
        """Delete secret."""
        secret_model = SecretModel.query.filter(SecretModel.key == key).first()
        if secret_model:
            db.session.delete(secret_model)
            try:
                db.session.commit()
            except Exception as e:
                raise ApiError(
                    error_code="delete_secret_error",
                    message=f"Could not delete secret with key: {key}. Original error is: {e}",
                ) from e
        else:
            raise ApiError(
                error_code="delete_secret_error",
                message=f"Cannot delete secret with key: {key}. Resource does not exist.",
                status_code=404,
            )

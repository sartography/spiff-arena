"""Secret_service."""
from typing import Optional

from flask_bpmn.api.api_error import ApiError
from flask_bpmn.models.db import db
from sqlalchemy.exc import IntegrityError

from spiffworkflow_backend.models.secret_model import SecretAllowedProcessPathModel
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

    def encrypt_key(self, plain_key: str) -> str:
        """Encrypt_key."""
        # flask_secret = current_app.secret_key
        # print("encrypt_key")
        ...

    def decrypt_key(self, encrypted_key: str) -> str:
        """Decrypt key."""
        ...

    @staticmethod
    def add_secret(
        key: str,
        value: str,
        creator_user_id: int,
    ) -> SecretModel:
        """Add_secret."""
        # encrypted_key = self.encrypt_key(key)
        secret_model = SecretModel(
            key=key, value=value, creator_user_id=creator_user_id
        )
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
    def get_secret(key: str) -> Optional[SecretModel]:
        """Get_secret."""
        secret: SecretModel = (
            db.session.query(SecretModel).filter(SecretModel.key == key).first()
        )
        if secret is not None:
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
        creator_user_id: Optional[int] = None,
    ) -> None:
        """Does this pass pre commit?"""
        secret_model = SecretModel.query.filter(SecretModel.key == key).first()
        if secret_model:
            if secret_model.creator_user_id == creator_user_id:
                secret_model.value = value
                db.session.add(secret_model)
                try:
                    db.session.commit()
                except Exception as e:
                    raise ApiError(
                        error_code="update_secret_error",
                        message=f"There was an error updating the secret with key: {key}, and value: {value}",
                    ) from e
            else:
                raise ApiError(
                    error_code="update_secret_error",
                    message=f"User: {creator_user_id} cannot update the secret with key : {key}",
                    status_code=401,
                )
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
            if secret_model.creator_user_id == user_id:
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
                    message=f"User: {user_id} cannot delete the secret with key : {key}",
                    status_code=401,
                )
        else:
            raise ApiError(
                error_code="delete_secret_error",
                message=f"Cannot delete secret with key: {key}. Resource does not exist.",
                status_code=404,
            )

    @staticmethod
    def add_allowed_process(
        secret_id: int, user_id: str, allowed_relative_path: str
    ) -> SecretAllowedProcessPathModel:
        """Add_allowed_process."""
        secret_model = SecretModel.query.filter(SecretModel.id == secret_id).first()
        if secret_model:
            if secret_model.creator_user_id == user_id:
                secret_process_model = SecretAllowedProcessPathModel(
                    secret_id=secret_model.id,
                    allowed_relative_path=allowed_relative_path,
                )
                assert secret_process_model  # noqa: S101
                db.session.add(secret_process_model)
                try:
                    db.session.commit()
                except IntegrityError as ie:
                    db.session.rollback()
                    raise ApiError(
                        error_code="add_allowed_process_error",
                        message=f"Error adding allowed_process with secret {secret_model.id}, "
                        f"and path: {allowed_relative_path}. Resource already exists. "
                        f"Original error is {ie}",
                        status_code=409,
                    ) from ie
                except Exception as e:
                    # TODO: should we call db.session.rollback() here?
                    # db.session.rollback()
                    raise ApiError(
                        error_code="add_allowed_process_error",
                        message=f"Could not create an allowed process for secret with key: {secret_model.key} "
                        f"with path: {allowed_relative_path}. "
                        f"Original error is {e}",
                    ) from e
                return secret_process_model
            else:
                raise ApiError(
                    error_code="add_allowed_process_error",
                    message=f"User: {user_id} cannot modify the secret with key : {secret_model.key}",
                    status_code=401,
                )
        else:
            raise ApiError(
                error_code="add_allowed_process_error",
                message=f"Cannot add allowed process to secret with key: {secret_id}. Resource does not exist.",
                status_code=404,
            )

    @staticmethod
    def delete_allowed_process(allowed_process_id: int, user_id: int) -> None:
        """Delete_allowed_process."""
        allowed_process = SecretAllowedProcessPathModel.query.filter(
            SecretAllowedProcessPathModel.id == allowed_process_id
        ).first()
        if allowed_process:
            secret = SecretModel.query.filter(
                SecretModel.id == allowed_process.secret_id
            ).first()
            assert secret  # noqa: S101
            if secret.creator_user_id == user_id:
                db.session.delete(allowed_process)
                try:
                    db.session.commit()
                except Exception as e:
                    raise ApiError(
                        error_code="delete_allowed_process_error",
                        message=f"There was an exception deleting allowed_process: {allowed_process_id}. "
                        f"Original error is: {e}",
                    ) from e
            else:
                raise ApiError(
                    error_code="delete_allowed_process_error",
                    message=f"User: {user_id} cannot delete the allowed_process with id : {allowed_process_id}",
                    status_code=401,
                )
        else:
            raise ApiError(
                error_code="delete_allowed_process_error",
                message=f"Cannot delete allowed_process: {allowed_process_id}. Resource does not exist.",
                status_code=404,
            )

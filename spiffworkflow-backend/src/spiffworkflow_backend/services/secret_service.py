import re

import sentry_sdk
from flask import current_app

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.secret_model import SecretModel


class SecretService:
    CIPHER_ENCODING = "ascii"

    @classmethod
    def _encrypt(cls, value: str) -> str:
        encrypted_bytes: bytes = b""
        if current_app.config.get("SPIFFWORKFLOW_BACKEND_ENCRYPTION_LIB") == "cryptography":
            # cryptography needs a bytes object
            value_as_bytes = str.encode(value)
            encrypted_bytes = current_app.config["CIPHER"].encrypt(value_as_bytes)
        else:
            encrypted_bytes = current_app.config["CIPHER"].encrypt(value)
        return encrypted_bytes.decode(cls.CIPHER_ENCODING)

    @classmethod
    def _decrypt(cls, value: str) -> str:
        bytes_to_decrypt = bytes(value, cls.CIPHER_ENCODING)
        decrypted_bytes: bytes = current_app.config["CIPHER"].decrypt(bytes_to_decrypt)
        return decrypted_bytes.decode(cls.CIPHER_ENCODING)

    @classmethod
    def add_secret(
        cls,
        key: str,
        value: str,
        user_id: int,
    ) -> SecretModel:
        value = cls._encrypt(value)
        secret_model = SecretModel(key=key, value=value, user_id=user_id)
        db.session.add(secret_model)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ApiError(
                error_code="create_secret_error",
                message=(
                    f"There was an error creating a secret with key: {key} and value"
                    f" ending with: {value[:-4]}. Original error is {e}"
                ),
            ) from e
        return secret_model

    @staticmethod
    def get_secret(key: str) -> SecretModel:
        secret = db.session.query(SecretModel).filter(SecretModel.key == key).first()
        if isinstance(secret, SecretModel):
            return secret
        else:
            raise ApiError(
                error_code="missing_secret_error",
                message=f"Unable to locate a secret with the name: {key}. ",
            )

    @classmethod
    def update_secret(
        cls,
        key: str,
        value: str,
        user_id: int | None = None,
        create_if_not_exists: bool | None = False,
    ) -> None:
        """Does this pass pre commit?"""
        secret_model = SecretModel.query.filter(SecretModel.key == key).first()
        if secret_model:
            value = cls._encrypt(value)
            secret_model.value = value
            db.session.add(secret_model)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise e
        elif create_if_not_exists:
            if user_id is None:
                raise ApiError(
                    error_code="update_secret_error_no_user_id",
                    message=f"Cannot update secret with key: {key}. Missing user id.",
                    status_code=404,
                )
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

    @classmethod
    def resolve_possibly_secret_value(cls, value: str) -> str:
        if "SPIFF_SECRET:" in value:
            spiff_secret_match = re.match(r".*SPIFF_SECRET:(?P<variable_name>\w+).*", value)
            if spiff_secret_match is not None:
                spiff_variable_name = spiff_secret_match.group("variable_name")
                secret = cls.get_secret(spiff_variable_name)
                with sentry_sdk.start_span(op="task", description="decrypt_secret"):
                    decrypted_value = cls._decrypt(secret.value)
                    return re.sub(r"\bSPIFF_SECRET:\w+", decrypted_value, value)
        return value

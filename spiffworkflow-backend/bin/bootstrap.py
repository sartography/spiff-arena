import os

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.process_api_blueprint import _get_process_model_for_instantiation
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.secret_service import SecretService


def _bootstrap_users() -> None:
    permissions = AuthorizationService.load_permissions_yaml()
    usernames_to_bootstrap = [k for k, v in permissions["users"].items() if v["service"] == "bootstrap"]

    for username in usernames_to_bootstrap:
        user = AuthorizationService.create_user_from_sign_in(
            {
                "iss": "bootstrap",
                "sub": username,
            }
        )

        db.session.add(user)

        if ServiceAccountModel.query.filter(ServiceAccountModel.user_id == user.id).first():
            continue

        api_key = ServiceAccountModel.generate_api_key()
        api_key_hash = ServiceAccountModel.hash_api_key(api_key)

        service_account = ServiceAccountModel(
            name=user.username,
            created_by_user_id=user.id,
            user=user,
            api_key_hash=api_key_hash,
        )

        db.session.add(service_account)

        api_key_name = f"SPIFFWORKFLOW_API_KEY_{username}"
        SecretService.add_secret(api_key_name, api_key, user.id)

        print(f"Bootstrapped user {username} with api key: {api_key}")

    db.session.commit()


def _run_bootstrap_process_model() -> None:
    process_model_name = os.environ.get("SPIFFWORKFLOW_BACKEND_BOOTSTRAP_PROCESS_MODEL")
    if not process_model_name:
        return

    username = os.environ.get("SPIFFWORKFLOW_BACKEND_BOOTSTRAP_USERNAME")
    if not username:
        raise Exception("Bootstrap user not specified.")

    user = UserModel.query.filter(UserModel.username == username).first()
    if not user:
        raise Exception(f"Bootstrap user '{username}' not found.")

    print(f"Running bootstrap process model {process_model_name} as {user.username}")

    process_model = _get_process_model_for_instantiation(process_model_name)
    ProcessInstanceService.create_and_run_process_instance(
        process_model=process_model,
        persistence_level="full",
        user=user,
    )

    db.session.commit()


def main() -> None:
    with create_app().app.app_context():
        _bootstrap_users()
        _run_bootstrap_process_model()


if __name__ == "__main__":
    main()

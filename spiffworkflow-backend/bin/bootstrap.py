import os

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.secret_service import SecretService

api_key_name = "SPIFFWORKFLOW_API_KEY"

def _tmp() -> None:
    svc = ServiceAccountModel.query.filter(ServiceAccountModel.name == "admin").first()
    if svc:
        db.session.delete(svc)
    db.session.commit()

    try:
        SecretService.delete_secret(api_key_name, 1)
    except:
        pass

def _bootstrap() -> None:
    admin_user = UserModel.query.filter(UserModel.username == "admin").first()
    if not admin_user:
        # TODO: create
        return

    if ServiceAccountModel.query.filter(ServiceAccountModel.user_id == admin_user.id).first():
        return

    api_key = ServiceAccountModel.generate_api_key()
    api_key_hash = ServiceAccountModel.hash_api_key(api_key)
    
    service_account = ServiceAccountModel(
        name="admin",
        created_by_user_id=admin_user.id,
        user=admin_user,
        api_key_hash=api_key_hash,
    )

    db.session.add(service_account)
    db.session.commit()

    SecretService.add_secret(api_key_name, api_key, admin_user.id)
    
    print(api_key)

def main() -> None:
    bootstrap_process_model = os.environ.get("SPIFFWORKFLOW_BACKEND_BOOTSTRAP_PROCESS_MODEL")
    #if not bootstrap_process_model:
    #    return
    app = create_app()
    with app.app.app_context():
        _tmp()
        _bootstrap()


if __name__ == "__main__":
    main()

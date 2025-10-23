import os

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.secret_service import SecretService

api_key_name = "SPIFFWORKFLOW_API_KEY"
api_key_username = "adminX"

def _tmp() -> None:
    svc = ServiceAccountModel.query.filter(ServiceAccountModel.name == api_key_username).first()
    if svc:
        db.session.delete(svc)
        
    usr = UserModel.query.filter(UserModel.username == api_key_username).first()
    if usr:
        db.session.delete(usr)
    
    db.session.commit()

    try:
        SecretService.delete_secret(api_key_name, 1)
    except:
        pass

def _bootstrap() -> None:
    admin_user = UserModel.query.filter(UserModel.username == api_key_username).first()
    if not admin_user:
        admin_user = UserModel(
            username=api_key_username,
            service="http://localhost:8000/openid",
            service_id=api_key_username,
        )
        db.session.add(admin_user)
        db.session.commit()

    if ServiceAccountModel.query.filter(ServiceAccountModel.user_id == admin_user.id).first():
        return

    api_key = ServiceAccountModel.generate_api_key()
    api_key_hash = ServiceAccountModel.hash_api_key(api_key)
    
    service_account = ServiceAccountModel(
        name=api_key_username,
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

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.models.service_account import SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE
from spiffworkflow_backend.models.service_account import SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE_ID_PREFIX
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.user_service import UserService


class ServiceAccountService:
    @classmethod
    def create_service_account(cls, name: str, service_account_creator: UserModel) -> ServiceAccountModel:
        api_key = ServiceAccountModel.generate_api_key()
        api_key_hash = ServiceAccountModel.hash_api_key(api_key)
        username = ServiceAccountModel.generate_username_for_related_user(name, service_account_creator.id)
        service_account_user = UserModel(
            username=username,
            email=f"{username}@spiff.service.account.example.com",
            service=SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE,
            service_id=f"{SPIFF_SERVICE_ACCOUNT_AUTH_SERVICE_ID_PREFIX}_{username}",
        )
        db.session.add(service_account_user)
        service_account = ServiceAccountModel(
            name=name,
            created_by_user_id=service_account_creator.id,
            api_key_hash=api_key_hash,
            user=service_account_user,
        )
        db.session.add(service_account)
        ServiceAccountModel.commit_with_rollback_on_exception()
        cls.associated_service_account_with_permissions(service_account_user, service_account_creator)
        service_account.api_key = api_key
        return service_account

    @classmethod
    def associated_service_account_with_permissions(
        cls, service_account_user: UserModel, service_account_creator: UserModel
    ) -> None:
        principal = UserService.create_principal(service_account_user.id)
        user_permissions = sorted(UserService.get_permission_targets_for_user(service_account_creator))

        permission_objects = []
        for user_permission in user_permissions:
            permission_objects.append(
                PermissionAssignmentModel(
                    principal_id=principal.id,
                    permission_target_id=user_permission[0],
                    permission=user_permission[1],
                    grant_type=user_permission[2],
                )
            )

        db.session.bulk_save_objects(permission_objects)
        ServiceAccountModel.commit_with_rollback_on_exception()

import argparse

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.active_user import ActiveUserModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_queue import ProcessInstanceQueueModel
from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel
from spiffworkflow_backend.models.refresh_token import RefreshTokenModel
from spiffworkflow_backend.models.secret_model import SecretModel
from spiffworkflow_backend.models.service_account import ServiceAccountModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_property import UserPropertyModel


def created_service_account_user_ids_for_user(user: UserModel) -> set[int]:
    service_accounts = ServiceAccountModel.query.filter_by(created_by_user_id=user.id).all()
    return {service_account.user_id for service_account in service_accounts if service_account.user_id != user.id}


def created_service_accounts_that_are_not_the_target_user(user: UserModel) -> list[ServiceAccountModel]:
    return [
        service_account
        for service_account in ServiceAccountModel.query.filter_by(created_by_user_id=user.id).all()
        if service_account.user_id != user.id
    ]


def deletion_plan_for_user(user: UserModel) -> dict[str, int]:
    return {
        "active_user": ActiveUserModel.query.filter_by(user_id=user.id).count(),
        "refresh_token": RefreshTokenModel.query.filter_by(user_id=user.id).count(),
        "user_property": UserPropertyModel.query.filter_by(user_id=user.id).count(),
        "human_task_user": HumanTaskUserModel.query.filter_by(user_id=user.id).count(),
        "human_task_completed_by": HumanTaskModel.query.filter_by(completed_by_user_id=user.id).count(),
        "human_task_actual_owner": HumanTaskModel.query.filter_by(actual_owner_id=user.id).count(),
        "process_instance_initiated": ProcessInstanceModel.query.filter_by(process_initiator_id=user.id).count(),
        "process_instance_event": ProcessInstanceEventModel.query.filter_by(user_id=user.id).count(),
        "message_instance": MessageInstanceModel.query.filter_by(user_id=user.id).count(),
        "process_instance_report": ProcessInstanceReportModel.query.filter_by(created_by_id=user.id).count(),
        "secret": SecretModel.query.filter_by(user_id=user.id).count(),
        "service_account_created_by": ServiceAccountModel.query.filter_by(created_by_user_id=user.id).count(),
        "service_account_backing_user": ServiceAccountModel.query.filter_by(user_id=user.id).count(),
        "service_account_backing_users_created_by_target": len(created_service_account_user_ids_for_user(user)),
    }


def print_deletion_plan(user: UserModel, plan: dict[str, int], delete_created_service_accounts: bool) -> None:
    print(f"Target user: {user.username} <{user.email}> (id={user.id})")
    print("Rows affected:")
    for name, count in plan.items():
        print(f"  {name}: {count}")
    if plan["service_account_backing_users_created_by_target"] > 0 and delete_created_service_accounts:
        print("Note: backing user rows for service accounts created by this user are not deleted by this script.")
    elif plan["service_account_backing_users_created_by_target"] > 0:
        print("Note: service accounts created by this user will block deletion unless explicitly handled.")


def confirm_deletion(email: str) -> bool:
    confirmation = input(f"Type the email address to permanently delete this user ({email}): ")
    return confirmation == email


def delete_user_completely(
    email: str,
    dry_run: bool = False,
    yes: bool = False,
    delete_created_service_accounts: bool = False,
) -> bool:
    """Delete a user and all their dependent records."""
    user = UserModel.query.filter_by(email=email).first()
    if not user:
        print(f"User not found: {email}")
        return False
    username = user.username
    plan = deletion_plan_for_user(user)
    print_deletion_plan(user, plan, delete_created_service_accounts)

    if dry_run:
        print("Dry run only. No rows were deleted.")
        return True

    blocking_service_accounts = created_service_accounts_that_are_not_the_target_user(user)
    if blocking_service_accounts and not delete_created_service_accounts:
        print(
            "Refusing to delete user because they created service accounts. "
            "Reassign those service accounts or rerun with --delete-created-service-accounts."
        )
        return False

    if not yes and not confirm_deletion(email):
        print("Confirmation did not match. No rows were deleted.")
        return False

    try:
        # Delete active user records
        ActiveUserModel.query.filter_by(user_id=user.id).delete()

        # Delete authentication/session metadata
        RefreshTokenModel.query.filter_by(user_id=user.id).delete()
        UserPropertyModel.query.filter_by(user_id=user.id).delete()

        # Delete human task user assignments
        HumanTaskUserModel.query.filter_by(user_id=user.id).delete()

        # Update human tasks to remove user references
        HumanTaskModel.query.filter_by(completed_by_user_id=user.id).update({"completed_by_user_id": None})
        HumanTaskModel.query.filter_by(actual_owner_id=user.id).update({"actual_owner_id": None})

        # Delete process instances initiated by user. Do not use bulk delete here:
        # the model's ORM cascades remove human_task and other dependent rows.
        process_instances = ProcessInstanceModel.query.filter_by(process_initiator_id=user.id).all()
        for process_instance in process_instances:
            ProcessInstanceQueueModel.query.filter_by(process_instance_id=process_instance.id).delete()
            db.session.delete(process_instance)

        # Delete process instance events
        ProcessInstanceEventModel.query.filter_by(user_id=user.id).delete()

        # Remove nullable references from message instances that belong to other process instances
        MessageInstanceModel.query.filter_by(user_id=user.id).update({"user_id": None})

        # Delete reports created by the user
        ProcessInstanceReportModel.query.filter_by(created_by_id=user.id).delete()

        # Delete secrets
        SecretModel.query.filter_by(user_id=user.id).delete()

        # Delete service accounts where this user is the backing auth user. Service accounts
        # merely created by this user are deleted only when explicitly requested.
        if delete_created_service_accounts:
            ServiceAccountModel.query.filter_by(created_by_user_id=user.id).delete()
        ServiceAccountModel.query.filter_by(user_id=user.id).delete()

        # Finally delete the user (cascade will handle principal and user_group_assignments)
        db.session.delete(user)
        db.session.commit()

        print(f"User {username} deleted successfully")
        return True

    except Exception as e:
        db.session.rollback()
        print(f"Error deleting user: {e}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Destructively delete a user and dependent records.")
    parser.add_argument("email", help="Email address of the user to delete.")
    parser.add_argument("--dry-run", action="store_true", help="Print affected row counts without deleting anything.")
    parser.add_argument("--yes", action="store_true", help="Skip the interactive confirmation prompt.")
    parser.add_argument(
        "--delete-created-service-accounts",
        action="store_true",
        help="Also delete service accounts created by the target user.",
    )
    args = parser.parse_args()

    app = create_app()
    with app.app.app_context():
        deleted = delete_user_completely(
            args.email,
            dry_run=args.dry_run,
            yes=args.yes,
            delete_created_service_accounts=args.delete_created_service_accounts,
        )
    if not deleted:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

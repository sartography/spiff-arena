"""Deletes all permissions and then re-imports from yaml file."""
from spiffworkflow_backend import get_hacked_up_app_for_script
from spiffworkflow_backend.services.authorization_service import AuthorizationService


def main() -> None:
    """Main."""
    app = get_hacked_up_app_for_script()
    with app.app_context():
        AuthorizationService.delete_all_permissions_and_recreate()


if __name__ == "__main__":
    main()

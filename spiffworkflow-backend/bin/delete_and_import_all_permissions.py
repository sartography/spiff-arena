"""Deletes all permissions and then re-imports from yaml file."""

from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.authorization_service import AuthorizationService


def main() -> None:
    """Main."""
    app = create_app()
    with app.app_context():
        AuthorizationService.delete_all_permissions()
        AuthorizationService.import_permissions_from_yaml_file()


if __name__ == "__main__":
    main()

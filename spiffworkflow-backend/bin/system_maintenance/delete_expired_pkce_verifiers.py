from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.authentication_service import PKCE


def main() -> None:
    app = create_app()

    with app.app.app_context():
        PKCE.delete_expired_pkce_code_verifiers()


if __name__ == "__main__":
    main()

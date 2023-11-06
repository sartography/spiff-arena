import sys

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.user_service import UserService


def main() -> None:
    app = create_app()
    process_model_identifier = sys.argv[1]

    with app.app_context():
        user = UserModel.query.first()
        if user is None:
            username = "testuser"
            user = UserService.create_user(username, "service", "service")
        process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model_identifier, user
        )
        execution_strategy_name = app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND"]
        ProcessInstanceService.run_process_instance_with_processor(
            process_instance, execution_strategy_name=execution_strategy_name
        )


if __name__ == "__main__":
    main()

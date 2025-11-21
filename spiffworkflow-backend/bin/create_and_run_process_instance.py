import json
import sys

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.user_service import UserService


def main() -> None:
    flask_app = create_app().app
    process_model_identifier = sys.argv[1].replace(":", "/")

    with flask_app.app_context():
        user = UserModel.query.first()
        if user is None:
            username = "testuser"
            user = UserService.create_user(username, "service", "service")
        process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            process_model_identifier, user
        )
        execution_strategy_name = flask_app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND"]
        ProcessInstanceService.run_process_instance_with_processor(
            process_instance, execution_strategy_name=execution_strategy_name
        )

        # Print the final task data
        final_data = process_instance.get_data()
        print("\nFinal Task Data:")
        print(json.dumps(final_data, indent=2))


if __name__ == "__main__":
    main()

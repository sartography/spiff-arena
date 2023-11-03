from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService


def main() -> None:
    app = create_app()
    with app.app_context():
        execution_strategy_name = app.config["SPIFFWORKFLOW_BACKEND_ENGINE_STEP_DEFAULT_STRATEGY_BACKGROUND"]
        process_instance = ProcessInstanceModel.query.filter_by(id=2).first()
        ProcessInstanceService.run_process_instance_with_processor(
            process_instance, execution_strategy_name=execution_strategy_name
        )


if __name__ == "__main__":
    main()

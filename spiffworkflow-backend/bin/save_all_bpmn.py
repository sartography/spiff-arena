"""Grabs tickets from csv and makes process instances."""

import os

from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.data_setup_service import DataSetupService


def main() -> None:
    app = create_app()
    with app.app_context():
        failing_process_models = DataSetupService.save_all_process_models()
        for bpmn_errors in failing_process_models:
            print(bpmn_errors)
        if os.environ.get("SPIFFWORKFLOW_BACKEND_FAIL_ON_INVALID_PROCESS_MODELS") != "false" and len(failing_process_models) > 0:
            exit(1)


if __name__ == "__main__":
    main()

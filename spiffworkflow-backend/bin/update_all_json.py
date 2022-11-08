"""Updates all JSON files, based on the current state of BPMN_SPEC_ABSOLUTE_DIR"""
from spiffworkflow_backend import get_hacked_up_app_for_script
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def main() -> None:
    """Main."""
    app = get_hacked_up_app_for_script()
    with app.app_context():

        groups = ProcessModelService().get_process_groups()
        for group in groups:
            for process_model in group.process_models:
                update_items = {
                    'process_group_id': '',
                    'id': f"{group.id}/{process_model.id}"
                }
                ProcessModelService().update_spec(process_model, update_items)


if __name__ == "__main__":
    main()

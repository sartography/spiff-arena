"""Grabs tickets from csv and makes process instances."""
import os

from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService

# from lxml.etree import Element as EtreeElement


def main():
    """Main."""
    os.environ["SPIFFWORKFLOW_BACKEND_ENV"] = "development"
    flask_env_key = "FLASK_SESSION_SECRET_KEY"
    os.environ[flask_env_key] = "whatevs"
    if "BPMN_SPEC_ABSOLUTE_DIR" not in os.environ:
        home = os.environ["HOME"]
        full_process_model_path = (
            f"{home}/projects/github/sartography/sample-process-models"
        )
        if os.path.isdir(full_process_model_path):
            os.environ["BPMN_SPEC_ABSOLUTE_DIR"] = full_process_model_path
        else:
            raise Exception(f"Could not find {full_process_model_path}")
    app = create_app()
    with app.app_context():
        no_primary = []
        failing_process_models = []
        process_models = ProcessModelService().get_process_models()
        for process_model in process_models:
            if process_model.primary_file_name:

                bpmn_xml_file_contents = SpecFileService.get_data(
                    process_model, process_model.primary_file_name
                )
                bad_files = [
                    "B.1.0.bpmn",
                    "C.1.0.bpmn",
                    "C.2.0.bpmn",
                    "C.6.0.bpmn",
                    "TC-5.1.bpmn",
                ]
                if process_model.primary_file_name in bad_files:
                    continue
                print(f"primary_file_name: {process_model.primary_file_name}")
                try:
                    SpecFileService.update_file(
                        process_model,
                        process_model.primary_file_name,
                        bpmn_xml_file_contents,
                    )
                except Exception as ex:
                    failing_process_models.append(
                        (process_model.primary_file_name, str(ex))
                    )
                # files = SpecFileService.get_files(
                #     process_model, extension_filter="bpmn"
                # )
                # bpmn_etree_element: EtreeElement = (
                #     SpecFileService.get_etree_element_from_binary_data(
                #         bpmn_xml_file_contents, process_model.primary_file_name
                #     )
                # )
                # if len(files) == 1:
                # try:
                #     new_bpmn_process_identifier = (
                #         SpecFileService.get_bpmn_process_identifier(
                #             bpmn_etree_element
                #         )
                #     )
                #     if (
                #         process_model.primary_process_id
                #         != new_bpmn_process_identifier
                #     ):
                #         print(
                #             "primary_process_id: ", process_model.primary_process_id
                #         )
                #         # attributes_to_update = {
                #         #     "primary_process_id": new_bpmn_process_identifier
                #         # }
                #         # ProcessModelService().update_spec(
                #         #     process_model, attributes_to_update
                #         # )
                # # except Exception as exception:
                # except Exception:
                #     print(f"BAD ONE: {process_model.id}")
                #     # raise exception
            else:
                no_primary.append(process_model)
        # for bpmn in no_primary:
        #     print(bpmn)
        for bpmn_errors in failing_process_models:
            print(bpmn_errors)
        if len(failing_process_models) > 0:
            exit(1)


if __name__ == "__main__":
    main()

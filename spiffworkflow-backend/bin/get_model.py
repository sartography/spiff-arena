
from spiffworkflow_backend import create_app
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


def main() -> None:
    app = create_app()
    with app.app_context():
        process_model_identifier = "site-administration/testkb/wip"
        process_model = ProcessModelService.get_process_model(process_model_identifier)
        files = FileSystemService.get_sorted_files(process_model)
        process_model.files = files

        for file in process_model.files:
            print("file", file)
            file.references = SpecFileService.get_references_for_file(file, process_model)


if __name__ == "__main__":
    main()

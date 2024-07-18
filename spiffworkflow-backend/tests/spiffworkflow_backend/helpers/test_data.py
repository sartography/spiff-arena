from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_model_service import ProcessModelService

from tests.spiffworkflow_backend.helpers.example_data import ExampleDataLoader


def assure_process_group_exists(process_group_id: str | None = None) -> ProcessGroup:
    process_group = None
    if process_group_id is not None:
        try:
            process_group = ProcessModelService.get_process_group(process_group_id)
        except ProcessEntityNotFoundError:
            process_group = None

    if process_group is None:
        process_group_id_to_create = "test_process_group"
        if process_group_id is not None:
            process_group_id_to_create = process_group_id
        process_group = ProcessGroup(
            id=process_group_id_to_create,
            display_name="Test Workflows",
            admin=False,
            display_order=0,
        )
        ProcessModelService.add_process_group(process_group)
    return process_group


def load_test_spec(
    process_model_id: str,
    bpmn_file_name: str | None = None,
    primary_file_name: str | None = None,
    process_model_source_directory: str | None = None,
) -> ProcessModelInfo:
    """Loads a bpmn file into the process model dir based on a directory in tests/data."""
    if process_model_source_directory is None:
        raise Exception("You must include a `process_model_source_directory`.")

    spec = ExampleDataLoader.create_spec(
        process_model_id=process_model_id,
        display_name=process_model_id,
        bpmn_file_name=bpmn_file_name,
        process_model_source_directory=process_model_source_directory,
        primary_file_name=primary_file_name,
    )
    return spec

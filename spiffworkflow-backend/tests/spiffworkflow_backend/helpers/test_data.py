"""User."""
from typing import Optional

from tests.spiffworkflow_backend.helpers.example_data import ExampleDataLoader

from spiffworkflow_backend.exceptions.process_entity_not_found_error import (
    ProcessEntityNotFoundError,
)
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def assure_process_group_exists(process_group_id: Optional[str] = None) -> ProcessGroup:
    """Assure_process_group_exists."""
    process_group = None
    process_model_service = ProcessModelService()
    if process_group_id is not None:
        try:
            process_group = process_model_service.get_process_group(process_group_id)
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
        process_model_service.add_process_group(process_group)
    return process_group


def load_test_spec(
    process_model_id: str,
    process_group_id: Optional[str] = None,
    bpmn_file_name: Optional[str] = None,
    process_model_source_directory: Optional[str] = None,
) -> ProcessModelInfo:
    """Loads a process model into the bpmn dir based on a directory in tests/data."""
    process_group = None
    process_model_service = ProcessModelService()
    if process_group_id is None:
        process_group_id = "test_process_group_id"
    process_group = assure_process_group_exists(process_group_id)
    process_group_id = process_group.id

    try:
        return process_model_service.get_process_model(
            process_model_id, group_id=process_group_id
        )
    except ProcessEntityNotFoundError:
        spec = ExampleDataLoader().create_spec(
            process_model_id=process_model_id,
            from_tests=True,
            display_name=process_model_id,
            process_group_id=process_group_id,
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory=process_model_source_directory,
        )
        return spec


# def user_info_to_query_string(user_info, redirect_url):
#     query_string_list = []
#     items = user_info.items()
#     for key, value in items:
#         query_string_list.append('%s=%s' % (key, urllib.parse.quote(value)))
#
#     query_string_list.append('redirect_url=%s' % redirect_url)
#
#     return '?%s' % '&'.join(query_string_list)

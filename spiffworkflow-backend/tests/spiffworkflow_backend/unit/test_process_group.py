"""Process Model."""

from flask.app import Flask
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def test_there_is_at_least_one_group_after_we_create_one(app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
    process_group = ProcessGroup(id="hey", display_name="sure")
    ProcessModelService.add_process_group(process_group)
    process_groups = ProcessModelService.get_process_groups()
    assert len(process_groups) > 0

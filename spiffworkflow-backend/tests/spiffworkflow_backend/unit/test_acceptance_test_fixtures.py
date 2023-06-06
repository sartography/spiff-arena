import os

from flask.app import Flask
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.acceptance_test_fixtures import load_acceptance_test_fixtures
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def test_start_dates_are_one_hour_apart(app: Flask) -> None:
    process_model_identifier = "misc/acceptance-tests-group-one/acceptance-tests-model-1"
    group_identifier = os.path.dirname(process_model_identifier)
    parent_group_identifier = os.path.dirname(group_identifier)
    if not ProcessModelService.is_process_group(parent_group_identifier):
        process_group = ProcessGroup(id=parent_group_identifier, display_name=parent_group_identifier)
        ProcessModelService.add_process_group(process_group)
    if not ProcessModelService.is_process_group(group_identifier):
        process_group = ProcessGroup(id=group_identifier, display_name=group_identifier)
        ProcessModelService.add_process_group(process_group)
    if not ProcessModelService.is_process_model(process_model_identifier):
        process_model = ProcessModelInfo(
            id=process_model_identifier,
            display_name=process_model_identifier,
            description="hey",
        )
        ProcessModelService.add_process_model(process_model)
    process_instances = load_acceptance_test_fixtures()

    assert len(process_instances) > 2
    assert process_instances[0].start_in_seconds is not None
    assert process_instances[1].start_in_seconds is not None
    assert (process_instances[0].start_in_seconds - 3600) == (process_instances[1].start_in_seconds)

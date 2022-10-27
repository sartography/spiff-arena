"""Test Permissions."""
from typing import Optional

from flask.app import Flask
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

# from tests.spiffworkflow_backend.helpers.test_data import find_or_create_process_group
# from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
# from spiffworkflow_backend.models.permission_target import PermissionTargetModel


def test_generate_report_with_filter_by(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    setup_process_instances_for_reports: list[ProcessInstanceModel],
) -> None:
    """Test_user_can_be_given_permission_to_administer_process_group."""
    process_instances = setup_process_instances_for_reports
    report_metadata = {
        "filter_by": [
            {"field_name": "grade_level", "operator": "equals", "field_value": 2}
        ]
    }
    results = do_report_with_metadata_and_instances(report_metadata, process_instances)
    assert len(results) == 2
    names = get_names_from_results(results)
    assert names == ["kay", "jay"]


def test_generate_report_with_filter_by_with_variable_substitution(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    setup_process_instances_for_reports: list[ProcessInstanceModel],
) -> None:
    """Test_user_can_be_given_permission_to_administer_process_group."""
    process_instances = setup_process_instances_for_reports
    report_metadata = {
        "filter_by": [
            {
                "field_name": "grade_level",
                "operator": "equals",
                "field_value": "{{grade_level}}",
            }
        ]
    }
    results = do_report_with_metadata_and_instances(
        report_metadata, process_instances, {"grade_level": 1}
    )
    assert len(results) == 1
    names = get_names_from_results(results)
    assert names == ["ray"]


def test_generate_report_with_order_by_and_one_field(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    setup_process_instances_for_reports: list[ProcessInstanceModel],
) -> None:
    """Test_user_can_be_given_permission_to_administer_process_group."""
    process_instances = setup_process_instances_for_reports
    report_metadata = {"order_by": ["test_score"]}
    results = do_report_with_metadata_and_instances(report_metadata, process_instances)
    assert len(results) == 3
    names = get_names_from_results(results)
    assert names == ["jay", "ray", "kay"]


def test_generate_report_with_order_by_and_two_fields(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    setup_process_instances_for_reports: list[ProcessInstanceModel],
) -> None:
    """Test_user_can_be_given_permission_to_administer_process_group."""
    process_instances = setup_process_instances_for_reports
    report_metadata = {"order_by": ["grade_level", "test_score"]}
    results = do_report_with_metadata_and_instances(report_metadata, process_instances)
    assert len(results) == 3
    names = get_names_from_results(results)
    assert names == ["ray", "jay", "kay"]


def test_generate_report_with_order_by_desc(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    setup_process_instances_for_reports: list[ProcessInstanceModel],
) -> None:
    """Test_user_can_be_given_permission_to_administer_process_group."""
    process_instances = setup_process_instances_for_reports
    report_metadata = {"order_by": ["grade_level", "-test_score"]}
    results = do_report_with_metadata_and_instances(report_metadata, process_instances)
    assert len(results) == 3
    names = get_names_from_results(results)
    assert names == ["ray", "kay", "jay"]


def test_generate_report_with_columns(
    app: Flask,
    with_db_and_bpmn_file_cleanup: None,
    setup_process_instances_for_reports: list[ProcessInstanceModel],
) -> None:
    """Test_user_can_be_given_permission_to_administer_process_group."""
    process_instances = setup_process_instances_for_reports
    report_metadata = {
        "columns": [
            {"Header": "Name", "accessor": "name"},
            {"Header": "Status", "accessor": "status"},
        ],
        "order_by": ["test_score"],
        "filter_by": [
            {"field_name": "grade_level", "operator": "equals", "field_value": 1}
        ],
    }
    results = do_report_with_metadata_and_instances(report_metadata, process_instances)
    assert len(results) == 1
    assert results == [{"name": "ray", "status": "complete"}]


def do_report_with_metadata_and_instances(
    report_metadata: dict,
    process_instances: list[ProcessInstanceModel],
    substitution_variables: Optional[dict] = None,
) -> list[dict]:
    """Do_report_with_metadata_and_instances."""
    process_instance_report = ProcessInstanceReportModel.create_with_attributes(
        identifier="sure",
        process_group_identifier=process_instances[0].process_group_identifier,
        process_model_identifier=process_instances[0].process_model_identifier,
        report_metadata=report_metadata,
        user=BaseTest.find_or_create_user(),
    )

    return process_instance_report.generate_report(
        process_instances, substitution_variables
    )["results"]


def get_names_from_results(results: list[dict]) -> list[str]:
    """Get_names_from_results."""
    return [result["name"] for result in results]

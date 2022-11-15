"""Test_process_instance_report_service."""
from flask import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_report_service import ProcessInstanceReportFilter
from spiffworkflow_backend.services.process_instance_report_service import ProcessInstanceReportService


class TestProcessInstanceReportService(BaseTest):
    """TestProcessInstanceReportService."""

    def _filter_from_metadata(self, report_metadata: dict) -> ProcessInstanceReportFilter:
        report = ProcessInstanceReportModel(
            identifier="test",
            created_by_id=1,
            report_metadata=report_metadata,
        )
        return ProcessInstanceReportService.filter_from_metadata(report)


    def test_report_with_no_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_report_with_no_filter."""
        report_filter = self._filter_from_metadata({
            "columns": [],
        })

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_empty_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_report_with_no_filter."""
        report_filter = self._filter_from_metadata({
            "columns": [],
            "filter_by": [],
        })

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None


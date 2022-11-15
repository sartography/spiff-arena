"""Test_process_instance_report_service."""
from flask import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

from spiffworkflow_backend.models.process_instance_report import (
    ProcessInstanceReportModel,
)
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportFilter,
)
from spiffworkflow_backend.services.process_instance_report_service import (
    ProcessInstanceReportService,
)


class TestProcessInstanceReportService(BaseTest):
    """TestProcessInstanceReportService."""

    def _filter_from_metadata(
        self, report_metadata: dict
    ) -> ProcessInstanceReportFilter:
        """Docstring."""
        report = ProcessInstanceReportModel(
            identifier="test",
            created_by_id=1,
            report_metadata=report_metadata,
        )
        return ProcessInstanceReportService.filter_from_metadata(report)

    def _filter_by_dict_from_metadata(
        self, report_metadata: dict
    ) -> ProcessInstanceReportFilter:
        """Docstring."""
        report = ProcessInstanceReportModel(
            identifier="test",
            created_by_id=1,
            report_metadata=report_metadata,
        )
        return ProcessInstanceReportService.filter_by_to_dict(report)

    def test_filter_by_to_dict_no_filter_by(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        filters = self._filter_by_dict_from_metadata(
            {
                "columns": [],
            }
        )

        assert filters == {}

    def test_filter_by_to_dict_empty_filter_by(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        filters = self._filter_by_dict_from_metadata(
            {
                "columns": [],
                "filter_by": [],
            }
        )

        assert filters == {}

    def test_filter_by_to_dict_single_filter_by(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        filters = self._filter_by_dict_from_metadata(
            {
                "columns": [],
                "filter_by": [{"field_name": "end_to", "field_value": "1234"}],
            }
        )

        assert filters == {"end_to": "1234"}

    def test_filter_by_to_dict_mulitple_filter_by(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        filters = self._filter_by_dict_from_metadata(
            {
                "columns": [],
                "filter_by": [
                    {"field_name": "end_to", "field_value": "1234"},
                    {"field_name": "end_from", "field_value": "4321"},
                ],
            }
        )

        assert filters == {"end_to": "1234", "end_from": "4321"}

    def test_report_with_no_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
            }
        )

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
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_unknown_filter_field_name(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [{"field_name": "bob", "field_value": "joe"}],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_unknown_filter_keys(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [{"_name": "bob", "_value": "joe"}],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_process_model_identifier_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [
                    {"field_name": "process_model_identifier", "field_value": "bob"}
                ],
            }
        )

        assert report_filter.process_model_identifier == "bob"
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_start_from_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [{"field_name": "start_from", "field_value": "1234"}],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from == 1234
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_start_to_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [{"field_name": "start_to", "field_value": "1234"}],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to == 1234
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_end_from_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [{"field_name": "end_from", "field_value": "1234"}],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from == 1234
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_with_end_to_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [{"field_name": "end_to", "field_value": "1234"}],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to == 1234
        assert report_filter.process_status is None

    def test_report_with_single_startus_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [{"field_name": "process_status", "field_value": "ready"}],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status == ["ready"]

    def test_report_with_multiple_startus_filters(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata(
            {
                "columns": [],
                "filter_by": [
                    {
                        "field_name": "process_status",
                        "field_value": "ready,completed,other",
                    }
                ],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status == ["ready", "completed", "other"]

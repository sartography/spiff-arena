"""Test_process_instance_report_service."""
from typing import Optional

from flask import Flask
from flask.testing import FlaskClient
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
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
from spiffworkflow_backend.services.user_service import UserService


class TestProcessInstanceReportFilter(BaseTest):
    """TestProcessInstanceReportFilter."""

    def test_empty_filter_to_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        d = ProcessInstanceReportFilter().to_dict()

        assert d == {}

    def test_string_value_filter_to_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        d = ProcessInstanceReportFilter(process_model_identifier="bob").to_dict()

        assert d == {"process_model_identifier": "bob"}

    def test_int_value_filter_to_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        d = ProcessInstanceReportFilter(
            start_from=1,
            start_to=2,
            end_from=3,
            end_to=4,
        ).to_dict()

        assert d == {
            "start_from": "1",
            "start_to": "2",
            "end_from": "3",
            "end_to": "4",
        }

    def test_list_single_value_filter_to_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        d = ProcessInstanceReportFilter(process_status=["bob"]).to_dict()

        assert d == {"process_status": "bob"}

    def test_list_multiple_value_filter_to_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        d = ProcessInstanceReportFilter(process_status=["joe", "bob", "sue"]).to_dict()

        assert d == {"process_status": "joe,bob,sue"}


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

    def _filter_from_metadata_with_overrides(
        self,
        report_metadata: dict,
        process_model_identifier: Optional[str] = None,
        start_from: Optional[int] = None,
        start_to: Optional[int] = None,
        end_from: Optional[int] = None,
        end_to: Optional[int] = None,
        process_status: Optional[str] = None,
    ) -> ProcessInstanceReportFilter:
        """Docstring."""
        report = ProcessInstanceReportModel(
            identifier="test",
            created_by_id=1,
            report_metadata=report_metadata,
        )
        return ProcessInstanceReportService.filter_from_metadata_with_overrides(
            process_instance_report=report,
            process_model_identifier=process_model_identifier,
            start_from=start_from,
            start_to=start_to,
            end_from=end_from,
            end_to=end_to,
            process_status=process_status,
        )

    def _filter_by_dict_from_metadata(self, report_metadata: dict) -> dict[str, str]:
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

    def test_report_with_multiple_filters(
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
                    {"field_name": "start_from", "field_value": "44"},
                    {"field_name": "end_from", "field_value": "55"},
                    {"field_name": "process_status", "field_value": "ready"},
                ],
            }
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from == 44
        assert report_filter.start_to is None
        assert report_filter.end_from == 55
        assert report_filter.end_to is None
        assert report_filter.process_status == ["ready"]

    def test_report_no_override_with_no_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
            },
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_override_with_no_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
            },
            end_to=54321,
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to == 54321
        assert report_filter.process_status is None

    def test_report_override_process_model_identifier_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [
                    {"field_name": "process_model_identifier", "field_value": "bob"}
                ],
            },
            process_model_identifier="joe",
        )

        assert report_filter.process_model_identifier == "joe"
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_override_start_from_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [{"field_name": "start_from", "field_value": "123"}],
            },
            start_from=321,
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from == 321
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_override_start_to_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [{"field_name": "start_to", "field_value": "123"}],
            },
            start_to=321,
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to == 321
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_override_end_from_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [{"field_name": "end_from", "field_value": "123"}],
            },
            end_from=321,
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from == 321
        assert report_filter.end_to is None
        assert report_filter.process_status is None

    def test_report_override_end_to_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [{"field_name": "end_to", "field_value": "123"}],
            },
            end_to=321,
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to == 321
        assert report_filter.process_status is None

    def test_report_override_process_status_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [
                    {"field_name": "process_status", "field_value": "joe,bob"}
                ],
            },
            process_status="sue",
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status == ["sue"]

    def test_report_override_mulitple_process_status_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [{"field_name": "process_status", "field_value": "sue"}],
            },
            process_status="joe,bob",
        )

        assert report_filter.process_model_identifier is None
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status == ["joe", "bob"]

    def test_report_override_does_not_override_other_filters(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [
                    {"field_name": "process_model_identifier", "field_value": "sue"},
                    {"field_name": "process_status", "field_value": "sue"},
                ],
            },
            process_status="joe,bob",
        )

        assert report_filter.process_model_identifier == "sue"
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status == ["joe", "bob"]

    def test_report_override_of_none_does_not_override_filter(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Docstring."""
        report_filter = self._filter_from_metadata_with_overrides(
            {
                "columns": [],
                "filter_by": [
                    {"field_name": "process_model_identifier", "field_value": "sue"},
                    {"field_name": "process_status", "field_value": "sue"},
                ],
            },
            process_status=None,
        )

        assert report_filter.process_model_identifier == "sue"
        assert report_filter.start_from is None
        assert report_filter.start_to is None
        assert report_filter.end_from is None
        assert report_filter.end_to is None
        assert report_filter.process_status == ["sue"]

    def test_can_filter_by_completed_instances_initiated_by_me(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_can_filter_by_completed_instances_initiated_by_me."""
        process_model_id = "runs_without_input/sample"
        bpmn_file_location = "sample"
        process_model = load_test_spec(
            process_model_id,
            process_model_source_directory=bpmn_file_location,
        )
        user_one = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="user_two")

        # Several processes to ensure they do not return in the result
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="waiting", user=user_one
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )

        process_instance_report = ProcessInstanceReportService.report_with_identifier(
            user=user_one,
            report_identifier="system_report_completed_instances_initiated_by_me",
        )
        report_filter = (
            ProcessInstanceReportService.filter_from_metadata_with_overrides(
                process_instance_report=process_instance_report,
                process_model_identifier=process_model.id,
            )
        )
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_filter=report_filter,
            process_instance_report=process_instance_report,
            user=user_one,
        )

        assert len(response_json["results"]) == 2
        assert response_json["results"][0]["process_initiator_id"] == user_one.id
        assert response_json["results"][1]["process_initiator_id"] == user_one.id
        assert response_json["results"][0]["status"] == "complete"
        assert response_json["results"][1]["status"] == "complete"

    def test_can_filter_by_completed_instances_with_tasks_completed_by_me(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_can_filter_by_completed_instances_with_tasks_completed_by_me."""
        process_model_id = "runs_without_input/sample"
        bpmn_file_location = "sample"
        process_model = load_test_spec(
            process_model_id,
            process_model_source_directory=bpmn_file_location,
        )
        user_one = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="user_two")

        # Several processes to ensure they do not return in the result
        process_instance_created_by_user_one_one = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="complete", user=user_one
            )
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        process_instance_created_by_user_one_three = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="waiting", user=user_one
            )
        )
        process_instance_created_by_user_two_one = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="complete", user=user_two
            )
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="waiting", user=user_two
        )

        human_task_for_user_one_one = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_one.id,
            completed_by_user_id=user_one.id,
        )
        human_task_for_user_one_two = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_two_one.id,
            completed_by_user_id=user_one.id,
        )
        human_task_for_user_one_three = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_three.id,
            completed_by_user_id=user_one.id,
        )
        human_task_for_user_two_one = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_one.id,
            completed_by_user_id=user_two.id,
        )
        human_task_for_user_two_two = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_two_one.id,
            completed_by_user_id=user_two.id,
        )
        human_task_for_user_two_three = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_three.id,
            completed_by_user_id=user_two.id,
        )
        db.session.add(human_task_for_user_one_one)
        db.session.add(human_task_for_user_one_two)
        db.session.add(human_task_for_user_one_three)
        db.session.add(human_task_for_user_two_one)
        db.session.add(human_task_for_user_two_two)
        db.session.add(human_task_for_user_two_three)
        db.session.commit()

        process_instance_report = ProcessInstanceReportService.report_with_identifier(
            user=user_one,
            report_identifier=(
                "system_report_completed_instances_with_tasks_completed_by_me"
            ),
        )
        report_filter = (
            ProcessInstanceReportService.filter_from_metadata_with_overrides(
                process_instance_report=process_instance_report,
                process_model_identifier=process_model.id,
            )
        )
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_filter=report_filter,
            process_instance_report=process_instance_report,
            user=user_one,
        )

        assert len(response_json["results"]) == 1
        assert response_json["results"][0]["process_initiator_id"] == user_two.id
        assert (
            response_json["results"][0]["id"]
            == process_instance_created_by_user_two_one.id
        )
        assert response_json["results"][0]["status"] == "complete"

    def test_can_filter_by_completed_instances_with_tasks_completed_by_my_groups(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_can_filter_by_completed_instances_with_tasks_completed_by_my_groups."""
        process_model_id = "runs_without_input/sample"
        bpmn_file_location = "sample"
        process_model = load_test_spec(
            process_model_id,
            process_model_source_directory=bpmn_file_location,
        )
        user_group_one = GroupModel(identifier="group_one")
        user_group_two = GroupModel(identifier="group_two")
        db.session.add(user_group_one)
        db.session.add(user_group_two)
        db.session.commit()

        user_one = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="user_two")
        user_three = self.find_or_create_user(username="user_three")
        UserService.add_user_to_group(user_one, user_group_one)
        UserService.add_user_to_group(user_two, user_group_one)
        UserService.add_user_to_group(user_three, user_group_two)

        # Several processes to ensure they do not return in the result
        process_instance_created_by_user_one_one = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="complete", user=user_one
            )
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        process_instance_created_by_user_one_three = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="waiting", user=user_one
            )
        )
        process_instance_created_by_user_two_one = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="complete", user=user_two
            )
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="waiting", user=user_two
        )

        human_task_for_user_group_one_one = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_one.id,
            lane_assignment_id=user_group_one.id,
        )
        human_task_for_user_group_one_two = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_three.id,
            lane_assignment_id=user_group_one.id,
        )
        human_task_for_user_group_one_three = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_two_one.id,
            lane_assignment_id=user_group_one.id,
        )
        human_task_for_user_group_two_one = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_two_one.id,
            lane_assignment_id=user_group_two.id,
        )
        human_task_for_user_group_two_two = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_one.id,
            lane_assignment_id=user_group_two.id,
        )
        db.session.add(human_task_for_user_group_one_one)
        db.session.add(human_task_for_user_group_one_two)
        db.session.add(human_task_for_user_group_one_three)
        db.session.add(human_task_for_user_group_two_one)
        db.session.add(human_task_for_user_group_two_two)
        db.session.commit()

        process_instance_report = ProcessInstanceReportService.report_with_identifier(
            user=user_one,
            report_identifier=(
                "system_report_completed_instances_with_tasks_completed_by_my_groups"
            ),
        )
        report_filter = (
            ProcessInstanceReportService.filter_from_metadata_with_overrides(
                process_instance_report=process_instance_report,
                process_model_identifier=process_model.id,
            )
        )
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_filter=report_filter,
            process_instance_report=process_instance_report,
            user=user_one,
        )

        assert len(response_json["results"]) == 2
        assert response_json["results"][0]["process_initiator_id"] == user_two.id
        assert (
            response_json["results"][0]["id"]
            == process_instance_created_by_user_two_one.id
        )
        assert response_json["results"][0]["status"] == "complete"
        assert response_json["results"][1]["process_initiator_id"] == user_one.id
        assert (
            response_json["results"][1]["id"]
            == process_instance_created_by_user_one_one.id
        )
        assert response_json["results"][1]["status"] == "complete"

    def test_can_filter_by_with_relation_to_me(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_can_filter_by_with_relation_to_me."""
        process_model_id = "runs_without_input/sample"
        bpmn_file_location = "sample"
        process_model = load_test_spec(
            process_model_id,
            process_model_source_directory=bpmn_file_location,
        )
        user_group_one = GroupModel(identifier="group_one")
        user_group_two = GroupModel(identifier="group_two")
        db.session.add(user_group_one)
        db.session.add(user_group_two)
        db.session.commit()

        user_one = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="user_two")
        user_three = self.find_or_create_user(username="user_three")
        UserService.add_user_to_group(user_one, user_group_one)
        UserService.add_user_to_group(user_two, user_group_one)
        UserService.add_user_to_group(user_three, user_group_two)

        # Several processes to ensure they do not return in the result
        process_instance_created_by_user_one_one = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="complete", user=user_one
            )
        )
        process_instance_created_by_user_one_two = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="complete", user=user_one
            )
        )
        process_instance_created_by_user_one_three = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="waiting", user=user_one
            )
        )
        process_instance_created_by_user_two_one = (
            self.create_process_instance_from_process_model(
                process_model=process_model, status="complete", user=user_two
            )
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )
        self.create_process_instance_from_process_model(
            process_model=process_model, status="waiting", user=user_two
        )

        human_task_for_user_group_one_one = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_one.id,
            lane_assignment_id=user_group_one.id,
        )
        human_task_for_user_group_one_two = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_three.id,
            lane_assignment_id=user_group_one.id,
        )
        human_task_for_user_group_one_three = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_two_one.id,
            lane_assignment_id=user_group_one.id,
        )
        human_task_for_user_group_two_one = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_two_one.id,
            lane_assignment_id=user_group_two.id,
        )
        human_task_for_user_group_two_two = HumanTaskModel(
            process_instance_id=process_instance_created_by_user_one_one.id,
            lane_assignment_id=user_group_two.id,
        )
        db.session.add(human_task_for_user_group_one_one)
        db.session.add(human_task_for_user_group_one_two)
        db.session.add(human_task_for_user_group_one_three)
        db.session.add(human_task_for_user_group_two_one)
        db.session.add(human_task_for_user_group_two_two)
        db.session.commit()

        UserService.add_user_to_human_tasks_if_appropriate(user_one)

        process_instance_report = ProcessInstanceReportService.report_with_identifier(
            user=user_one
        )
        report_filter = (
            ProcessInstanceReportService.filter_from_metadata_with_overrides(
                process_instance_report=process_instance_report,
                process_model_identifier=process_model.id,
                with_relation_to_me=True,
            )
        )
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_filter=report_filter,
            process_instance_report=process_instance_report,
            user=user_one,
        )

        assert len(response_json["results"]) == 4
        process_instance_ids_in_results = [r["id"] for r in response_json["results"]]
        assert (
            process_instance_created_by_user_one_one.id
            in process_instance_ids_in_results
        )
        assert (
            process_instance_created_by_user_one_two.id
            in process_instance_ids_in_results
        )
        assert (
            process_instance_created_by_user_one_three.id
            in process_instance_ids_in_results
        )
        assert (
            process_instance_created_by_user_two_one.id
            in process_instance_ids_in_results
        )

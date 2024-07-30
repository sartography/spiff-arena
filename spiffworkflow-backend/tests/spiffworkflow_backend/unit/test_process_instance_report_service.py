import pytest
from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.process_instance_report import ReportMetadata
from spiffworkflow_backend.services.process_instance_report_service import ProcessInstanceReportMetadataInvalidError
from spiffworkflow_backend.services.process_instance_report_service import ProcessInstanceReportService
from spiffworkflow_backend.services.user_service import UserService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstanceReportService(BaseTest):
    def test_can_filter_by_completed_instances_initiated_by_me(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_id = "runs_without_input/sample"
        bpmn_file_location = "sample"
        process_model = load_test_spec(
            process_model_id,
            process_model_source_directory=bpmn_file_location,
        )
        user_one = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="user_two")

        # Several processes to ensure they do not return in the result
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_one)
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_one)
        self.create_process_instance_from_process_model(process_model=process_model, status="waiting", user=user_one)
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_two)
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_two)

        process_instance_report = ProcessInstanceReportService.report_with_identifier(
            user=user_one,
            report_identifier="system_report_completed_instances_initiated_by_me",
        )
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_metadata=process_instance_report.report_metadata,
            user=user_one,
        )

        assert len(response_json["results"]) == 2
        assert response_json["results"][0]["process_initiator_id"] == user_one.id
        assert response_json["results"][1]["process_initiator_id"] == user_one.id
        assert response_json["results"][0]["status"] == "complete"
        assert response_json["results"][1]["status"] == "complete"

    def test_raises_if_filtering_with_both_task_i_can_complete_and_tasks_completed_by_me(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user_one = self.find_or_create_user(username="user_one")
        report_metadata: ReportMetadata = {
            "columns": [],
            "filter_by": [
                {"field_name": "instances_with_tasks_waiting_for_me", "field_value": True, "operator": "equals"},
                {"field_name": "instances_with_tasks_completed_by_me", "field_value": True, "operator": "equals"},
            ],
            "order_by": [],
        }
        with pytest.raises(ProcessInstanceReportMetadataInvalidError):
            ProcessInstanceReportService.run_process_instance_report(
                report_metadata=report_metadata,
                user=user_one,
            )

    def test_with_group_identifier_does_not_conflict_with_system_filters(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        user_one = self.find_or_create_user(username="user_one")
        report_metadata: ReportMetadata = {
            "columns": [],
            "filter_by": [
                {"field_name": "instances_with_tasks_waiting_for_me", "field_value": True, "operator": "equals"},
                {"field_name": "user_group_identifier", "field_value": "group_one", "operator": "equals"},
            ],
            "order_by": [],
        }
        result = ProcessInstanceReportService.run_process_instance_report(
            report_metadata=report_metadata,
            user=user_one,
        )
        assert result is not None

        report_metadata = {
            "columns": [],
            "filter_by": [
                {"field_name": "instances_with_tasks_completed_by_me", "field_value": True, "operator": "equals"},
                {"field_name": "user_group_identifier", "field_value": "group_one", "operator": "equals"},
            ],
            "order_by": [],
        }
        result = ProcessInstanceReportService.run_process_instance_report(
            report_metadata=report_metadata,
            user=user_one,
        )
        assert result is not None

    def test_can_filter_by_completed_instances_with_tasks_completed_by_me(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model_id = "runs_without_input/sample"
        bpmn_file_location = "sample"
        process_model = load_test_spec(
            process_model_id,
            process_model_source_directory=bpmn_file_location,
        )
        user_one = self.find_or_create_user(username="user_one")
        user_two = self.find_or_create_user(username="user_two")

        # Several processes to ensure they do not return in the result
        process_instance_created_by_user_one_one = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_one)
        process_instance_created_by_user_one_three = self.create_process_instance_from_process_model(
            process_model=process_model, status="waiting", user=user_one
        )
        process_instance_created_by_user_two_one = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_two)
        self.create_process_instance_from_process_model(process_model=process_model, status="waiting", user=user_two)

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
            report_identifier="system_report_completed_instances_with_tasks_completed_by_me",
        )
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_metadata=process_instance_report.report_metadata,
            user=user_one,
        )

        assert len(response_json["results"]) == 1
        assert response_json["results"][0]["process_initiator_id"] == user_two.id
        assert response_json["results"][0]["id"] == process_instance_created_by_user_two_one.id
        assert response_json["results"][0]["status"] == "complete"

    def test_can_filter_by_completed_instances_with_tasks_completed_by_my_groups(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
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
        process_instance_created_by_user_one_one = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_one)
        process_instance_created_by_user_one_three = self.create_process_instance_from_process_model(
            process_model=process_model, status="waiting", user=user_one
        )
        process_instance_created_by_user_two_one = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_two)
        self.create_process_instance_from_process_model(process_model=process_model, status="waiting", user=user_two)

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
            report_identifier="system_report_completed_instances",
        )
        process_instance_report.report_metadata["filter_by"].append(
            {"field_name": "user_group_identifier", "field_value": user_one.groups[0].identifier}
        )
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_metadata=process_instance_report.report_metadata,
            user=user_one,
        )

        assert len(response_json["results"]) == 2
        assert response_json["results"][0]["process_initiator_id"] == user_two.id
        assert response_json["results"][0]["id"] == process_instance_created_by_user_two_one.id
        assert response_json["results"][0]["status"] == "complete"
        assert response_json["results"][1]["process_initiator_id"] == user_one.id
        assert response_json["results"][1]["id"] == process_instance_created_by_user_one_one.id
        assert response_json["results"][1]["status"] == "complete"

    def test_can_filter_by_with_relation_to_me(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
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
        process_instance_created_by_user_one_one = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        process_instance_created_by_user_one_two = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_one
        )
        process_instance_created_by_user_one_three = self.create_process_instance_from_process_model(
            process_model=process_model, status="waiting", user=user_one
        )
        process_instance_created_by_user_two_one = self.create_process_instance_from_process_model(
            process_model=process_model, status="complete", user=user_two
        )
        self.create_process_instance_from_process_model(process_model=process_model, status="complete", user=user_two)
        self.create_process_instance_from_process_model(process_model=process_model, status="waiting", user=user_two)

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

        new_group_ids = {g.id for g in user_one.groups}
        UserService.update_human_task_assignments_for_user(user_one, new_group_ids=new_group_ids, old_group_ids=set())

        process_instance_report = ProcessInstanceReportService.report_with_identifier(user=user_one)
        report_metadata = process_instance_report.report_metadata
        report_metadata["filter_by"].append({"field_name": "with_relation_to_me", "field_value": True, "operator": "equals"})
        response_json = ProcessInstanceReportService.run_process_instance_report(
            report_metadata=report_metadata,
            user=user_one,
        )

        assert len(response_json["results"]) == 4
        process_instance_ids_in_results = [r["id"] for r in response_json["results"]]
        assert process_instance_created_by_user_one_one.id in process_instance_ids_in_results
        assert process_instance_created_by_user_one_two.id in process_instance_ids_in_results
        assert process_instance_created_by_user_one_three.id in process_instance_ids_in_results
        assert process_instance_created_by_user_two_one.id in process_instance_ids_in_results

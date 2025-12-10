"""Test that call activities respect data store scoping based on caller's process group."""

import time

from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data_store import JSONDataStoreModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestCallActivityDataStoreScope(BaseTest):
    def test_called_process_uses_caller_location_for_data_store_access(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test data store access behavior in call activities.

        ACTUAL BEHAVIOR (verified by this test):
        When a process in 'site-administration' calls a process in 'finance' via Call Activity,
        the called process uses the CALLER's location (site-administration) for data store lookups.

        This is because tld.process_model_identifier remains set to the top-level process identifier
        throughout execution, even when inside call activity subprocesses.
        """
        self.create_process_group("site-administration", "Site Administration")
        self.create_process_group("finance", "Finance")

        # This must be loaded before the caller so it's registered in the reference_cache
        load_test_spec(
            process_model_id="finance/callee",
            process_model_source_directory="call_activity_ds_scope_callee",
            primary_file_name="callee.bpmn",
        )

        caller_model = load_test_spec(
            process_model_id="site-administration/caller",
            process_model_source_directory="call_activity_ds_scope_caller",
            primary_file_name="caller.bpmn",
        )

        current_time = round(time.time())

        # Test: Data store at caller's location should be accessible
        # This proves whether call activities use caller's or callee's location
        ds_admin = JSONDataStoreModel(
            identifier="test_data_store",
            location="site-administration",
            name="Admin Data Store",
            schema={},
            description="Data store in site-administration group",
            data={"key": "admin_value"},
            updated_at_in_seconds=current_time,
            created_at_in_seconds=current_time,
        )
        db.session.add(ds_admin)
        db.session.commit()

        # Run the caller process - if it completes, callee is using caller's location
        process_instance = self.create_process_instance_from_process_model(
            process_model=caller_model,
            user=with_super_admin_user,
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        assert process_instance.status == ProcessInstanceStatus.complete.value, (
            "UNEXPECTED: Call activity uses callee's own location (finance). "
            "Expected it to use caller's location (site-administration)."
        )

        assert processor.bpmn_process_instance.data["result_value"] == "admin_value", (
            "Call activity accessed data store but got wrong value"
        )

        db.session.delete(ds_admin)
        db.session.commit()

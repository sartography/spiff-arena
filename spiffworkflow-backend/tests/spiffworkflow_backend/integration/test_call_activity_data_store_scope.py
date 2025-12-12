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
    def test_called_process_uses_called_process_location_for_data_store_access(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test data store access behavior in call activities.

        ACTUAL BEHAVIOR (verified by this test):
        When a process in 'site-administration' calls a process in 'finance' via Call Activity,
        the called process uses the CALLED PROCESS's location (finance) for data store lookups.

        This allows reusable processes to have their own data stores defined in their own process groups.
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

        # Test: Data store at CALLED process location should be accessible
        # This proves whether call activities use caller's or callee's location
        ds_finance = JSONDataStoreModel(
            identifier="test_data_store",
            location="finance",
            name="Finance Data Store",
            schema={},
            description="Data store in finance group",
            data={"key": "finance_value"},
            updated_at_in_seconds=current_time,
            created_at_in_seconds=current_time,
        )
        db.session.add(ds_finance)
        db.session.commit()

        # Run the caller process - if it completes, callee is using callee's location (finance)
        process_instance = self.create_process_instance_from_process_model(
            process_model=caller_model,
            user=with_super_admin_user,
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        assert process_instance.status == ProcessInstanceStatus.complete.value, (
            "UNEXPECTED: Call activity failed to find data store in 'finance'. "
            "Expected it to use called process location (finance)."
        )

        assert processor.bpmn_process_instance.data["result_value"] == "finance_value", (
            "Call activity accessed data store but got wrong value. "
            f"Expected 'finance_value', got '{processor.bpmn_process_instance.data.get('result_value')}'"
        )

        db.session.delete(ds_finance)
        db.session.commit()

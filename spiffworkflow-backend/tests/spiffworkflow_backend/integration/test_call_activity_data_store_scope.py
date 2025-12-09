"""Test that call activities respect data store scoping based on callee's process group."""

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
    """Test call activity data store scoping behavior."""

    def test_called_process_uses_own_group_for_data_store_access(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test that a called process uses its own process group for data store searches, not the caller's group.

        When a process in 'site-administration' calls a process in 'finance' via Call Activity,
        the called process ('finance') should only be able to access data stores in its own hierarchy,
        not data stores from the caller's hierarchy ('site-administration').
        """
        # Create process groups
        self.create_process_group("site-administration", "Site Administration")
        self.create_process_group("finance", "Finance")

        # Load the callee process model FIRST in finance group
        # This must be loaded before the caller so it's registered in the reference_cache
        callee_model = load_test_spec(
            process_model_id="finance/callee",
            process_model_source_directory="call_activity_ds_scope_callee",
            primary_file_name="callee.bpmn",
        )

        # Load the caller process model in site-administration group
        # The caller references the callee via Call Activity
        caller_model = load_test_spec(
            process_model_id="site-administration/caller",
            process_model_source_directory="call_activity_ds_scope_caller",
            primary_file_name="caller.bpmn",
        )

        current_time = round(time.time())

        # Case 1: Data store is in the callee's process group ('finance').
        # The workflow should succeed as the data store is in scope.
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

        # Run the caller process which will call the finance process
        process_instance = self.create_process_instance_from_process_model(
            process_model=caller_model,
            user=with_super_admin_user,
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        # The process should complete successfully and the callee should have accessed the finance data store
        assert process_instance.status == ProcessInstanceStatus.complete.value
        assert processor.bpmn_process_instance.data["result_value"] == "finance_value"

        # Clean up
        db.session.delete(ds_finance)
        db.session.commit()

        # Case 2: Data store is in the caller's process group ('site-administration').
        # The workflow should fail as the data store is out of scope for the callee.
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

        # Run the caller process again
        process_instance2 = self.create_process_instance_from_process_model(
            process_model=caller_model,
            user=with_super_admin_user,
        )
        processor2 = ProcessInstanceProcessor(process_instance2)
        processor2.do_engine_steps(save=True, execution_strategy_name="greedy")

        # The process should fail because the callee cannot access the caller's data store
        assert process_instance2.status == ProcessInstanceStatus.error.value

        # Clean up
        db.session.delete(ds_admin)
        db.session.commit()

        # Case 3: Data store is at the root level (shared).
        # The workflow should succeed as both processes can access root-level data stores.
        ds_root = JSONDataStoreModel(
            identifier="test_data_store",
            location="",
            name="Root Data Store",
            schema={},
            description="Data store at root level",
            data={"key": "root_value"},
            updated_at_in_seconds=current_time,
            created_at_in_seconds=current_time,
        )
        db.session.add(ds_root)
        db.session.commit()

        # Run the caller process once more
        process_instance3 = self.create_process_instance_from_process_model(
            process_model=caller_model,
            user=with_super_admin_user,
        )
        processor3 = ProcessInstanceProcessor(process_instance3)
        processor3.do_engine_steps(save=True, execution_strategy_name="greedy")

        # The process should complete successfully accessing the root-level data store
        assert process_instance3.status == ProcessInstanceStatus.complete.value
        assert processor3.bpmn_process_instance.data["result_value"] == "root_value"

        # Clean up
        db.session.delete(ds_root)
        db.session.commit()

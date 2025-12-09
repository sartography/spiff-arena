"""Test for orphaned child task references bug."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestOrphanedChildren(BaseTest):
    """Test suite for orphaned child task references."""

    def test_parallel_gateway_with_failing_service_task_for_orphaned_children(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test if parallel gateway with failing service task creates orphaned child references.

        This test checks for the bug where a parent task's properties_json["children"]
        array contains GUIDs of child tasks that don't exist in the database.

        The scenario:
        1. Parallel gateway creates 3 child branches
        2. One branch has a service task that fails
        3. Check if the gateway task has children references that don't exist in DB
        """
        # Load the BPMN with parallel gateway and failing service task
        process_model = load_test_spec(
            process_model_id="test/orphaned_children",
            bpmn_file_name="parallel_gateway_fail.bpmn",
            process_model_source_directory="orphaned_children_repro",
        )

        # Create and run process instance
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)

        # Expect the process to fail due to service task error
        with pytest.raises(WorkflowExecutionServiceError) as exc_info:
            processor.do_engine_steps(save=True)

        # Verify error occurred
        assert exc_info.value is not None
        print(f"\n✓ Process failed as expected: {exc_info.value}")

        # Refresh the process instance to get latest data
        db.session.refresh(process_instance)

        # Get all tasks for this process instance
        all_tasks = TaskModel.query.filter_by(process_instance_id=process_instance.id).all()

        print(f"\n📊 Total tasks in database: {len(all_tasks)}")

        # Build a set of existing task GUIDs
        existing_task_guids = {task.guid for task in all_tasks}

        # Check each task's children references
        orphaned_references = []
        for task in all_tasks:
            if "children" not in task.properties_json:
                continue

            children_guids = task.properties_json["children"]
            if not children_guids:
                continue

            task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"

            # Check if any child doesn't exist in database
            missing_children = []
            for child_guid in children_guids:
                if child_guid not in existing_task_guids:
                    missing_children.append(child_guid)

            if missing_children:
                orphaned_references.append(
                    {
                        "parent_guid": task.guid,
                        "parent_task_def": task_def,
                        "parent_state": task.state,
                        "children_count": len(children_guids),
                        "orphaned_children": missing_children,
                    }
                )

        # Print detailed report
        print(f"\n{'=' * 80}")
        if orphaned_references:
            print("🐛 BUG REPRODUCED: Orphaned child references found!")
            print(f"{'=' * 80}")
            for ref in orphaned_references:
                print(f"\nParent Task: {ref['parent_task_def']}")
                print(f"  GUID: {ref['parent_guid']}")
                print(f"  State: {ref['parent_state']}")
                print(f"  Total children in JSON: {ref['children_count']}")
                print(f"  Orphaned children ({len(ref['orphaned_children'])}):")
                for orphaned_child in ref["orphaned_children"]:
                    print(f"    ✗ {orphaned_child} (NOT IN DATABASE)")

            # Print task tree for debugging
            print(f"\n{'=' * 80}")
            print("Task Tree (for debugging):")
            print(f"{'=' * 80}")
            for task in all_tasks:
                task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"
                print(f"\n{task_def} [{task.state}]")
                print(f"  GUID: {task.guid}")
                if "children" in task.properties_json:
                    children = task.properties_json["children"]
                    if children:
                        print(f"  Children ({len(children)}):")
                        for child_guid in children:
                            exists = "✓" if child_guid in existing_task_guids else "✗ MISSING"
                            print(f"    {exists} {child_guid}")

            # Fail the test to make the bug visible
            pytest.fail(
                f"Found {len(orphaned_references)} task(s) with orphaned child "
                f"references. This is the bug we're trying to reproduce!"
            )
        else:
            print("✅ No orphaned child references found")
            print("All child references exist in the database")
            print(f"{'=' * 80}")
            # This is actually unexpected - the bug should occur
            # But we won't fail the test, just note it
            print("\n⚠️  Note: Expected to reproduce orphaned children bug but didn't.")
            print("This could mean:")
            print("1. The bug has been fixed")
            print("2. This scenario doesn't trigger the bug")
            print("3. The timing is different than expected")

    def test_check_for_orphaned_children_in_error_state_tasks(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test specifically checking ERROR state tasks for orphaned children.

        Based on the code analysis, tasks in ERROR state are still saved to
        the database. This test ensures that ERROR tasks don't have orphaned
        child references.
        """
        process_model = load_test_spec(
            process_model_id="test/orphaned_error",
            bpmn_file_name="parallel_gateway_fail.bpmn",
            process_model_source_directory="orphaned_children_repro",
        )

        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)

        with pytest.raises(WorkflowExecutionServiceError):
            processor.do_engine_steps(save=True)

        db.session.refresh(process_instance)

        # Find tasks in ERROR state
        error_tasks = TaskModel.query.filter_by(process_instance_id=process_instance.id, state="ERROR").all()

        print(f"\n📊 Tasks in ERROR state: {len(error_tasks)}")

        if len(error_tasks) == 0:
            pytest.skip("No ERROR tasks found - cannot test this scenario")

        # Get all task GUIDs
        all_tasks = TaskModel.query.filter_by(process_instance_id=process_instance.id).all()
        existing_guids = {t.guid for t in all_tasks}

        # Check ERROR tasks for orphaned children
        for error_task in error_tasks:
            task_def = error_task.task_definition.bpmn_identifier if error_task.task_definition else "UNKNOWN"
            print(f"\nERROR Task: {task_def}")
            print(f"  GUID: {error_task.guid}")

            if "children" in error_task.properties_json:
                children = error_task.properties_json["children"]
                print(f"  Children in JSON: {len(children)}")

                for child_guid in children:
                    if child_guid not in existing_guids:
                        print(f"    ✗ ORPHANED: {child_guid}")
                        pytest.fail(f"ERROR task {task_def} has orphaned child reference: {child_guid}")
                    else:
                        print(f"    ✓ Exists: {child_guid}")
            else:
                print("  No children in JSON")

        print("\n✅ All ERROR tasks have valid child references")

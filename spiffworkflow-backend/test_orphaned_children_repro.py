#!/usr/bin/env python3
"""
Test script to check for orphaned child task references.

This script will:
1. Run a process instance with a failing service task
2. Query the database after the failure
3. Check if any tasks have children references that don't exist in the DB
"""

import sys
from typing import Any

from flask import Flask
from flask.testing import FlaskClient as TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class OrphanedChildrenChecker:
    """Helper class to check for orphaned child references."""

    @staticmethod
    def check_for_orphaned_children(process_instance_id: int) -> dict[str, Any]:
        """
        Check if any tasks have child references that don't exist in the database.

        Returns a dict with:
        - orphaned_count: Number of orphaned references found
        - orphaned_details: List of dicts with parent/child info
        - all_tasks: Total number of tasks
        """
        # Get all tasks for this process instance
        tasks = TaskModel.query.filter_by(process_instance_id=process_instance_id).all()

        # Build a set of existing task GUIDs
        existing_task_guids = {task.guid for task in tasks}

        # Check each task's children references
        orphaned_references = []
        for task in tasks:
            if "children" in task.properties_json and task.properties_json["children"]:
                children_guids = task.properties_json["children"]
                for child_guid in children_guids:
                    if child_guid not in existing_task_guids:
                        orphaned_references.append({
                            "parent_guid": task.guid,
                            "parent_task_spec": task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN",
                            "parent_state": task.state,
                            "orphaned_child_guid": child_guid,
                            "parent_children_count": len(children_guids),
                        })

        return {
            "orphaned_count": len(orphaned_references),
            "orphaned_details": orphaned_references,
            "all_tasks": len(tasks),
            "task_guids": list(existing_task_guids),
        }

    @staticmethod
    def print_report(result: dict[str, Any]) -> None:
        """Print a formatted report of orphaned children."""
        print("\n" + "=" * 80)
        print("ORPHANED CHILD REFERENCE CHECK")
        print("=" * 80)
        print(f"\nTotal tasks in database: {result['all_tasks']}")
        print(f"Orphaned child references found: {result['orphaned_count']}")

        if result["orphaned_count"] > 0:
            print("\n" + "-" * 80)
            print("ORPHANED REFERENCES (BUG CONFIRMED):")
            print("-" * 80)
            for ref in result["orphaned_details"]:
                print(f"\n  Parent Task: {ref['parent_task_spec']}")
                print(f"    GUID: {ref['parent_guid']}")
                print(f"    State: {ref['parent_state']}")
                print(f"    Children Count: {ref['parent_children_count']}")
                print(f"    ORPHANED Child GUID: {ref['orphaned_child_guid']}")
                print(f"    ^--- This child does NOT exist in the database!")
        else:
            print("\n✓ No orphaned references found - all children exist in database")

        print("\n" + "=" * 80)


def test_with_parallel_gateway_bpmn(app: Flask, client: TestClient) -> None:
    """Test the parallel gateway BPMN that user provided."""
    print("\n\nTEST 1: Parallel Gateway with Failing Service Task")
    print("-" * 80)

    # Load the BPMN file (you'll need to save it to the test data directory)
    # For now, we'll use a similar test
    try:
        process_model = load_test_spec(
            process_model_id="test/orphaned_parallel",
            bpmn_file_name="parallel_gateway_with_failing_service.bpmn",
            # You would need to save your BPMN file to the test data directory
        )
    except Exception as e:
        print(f"Could not load BPMN (expected if file not set up): {e}")
        return

    # Create process instance
    base_test = BaseTest()
    process_instance = base_test.create_process_instance_from_process_model(
        process_model=process_model
    )

    # Run the process - expect it to fail
    processor = ProcessInstanceProcessor(process_instance)
    error_occurred = False
    try:
        processor.do_engine_steps(save=True)
    except WorkflowExecutionServiceError as e:
        error_occurred = True
        print(f"✓ Expected error occurred: {type(e).__name__}")

    if not error_occurred:
        print("⚠ Warning: Expected WorkflowExecutionServiceError but none occurred")

    # Check for orphaned children
    db.session.refresh(process_instance)
    result = OrphanedChildrenChecker.check_for_orphaned_children(process_instance.id)
    OrphanedChildrenChecker.print_report(result)

    # Print task tree for debugging
    print("\n\nTask Tree:")
    print("-" * 80)
    tasks = TaskModel.query.filter_by(process_instance_id=process_instance.id).all()
    for task in tasks:
        task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"
        children = task.properties_json.get("children", [])
        print(f"{task_def} ({task.guid[:8]}...) [{task.state}]")
        if children:
            print(f"  Children: {len(children)}")
            for child_guid in children:
                child_exists = TaskModel.query.filter_by(guid=child_guid).first()
                status = "✓ EXISTS" if child_exists else "✗ MISSING"
                print(f"    - {child_guid[:8]}... {status}")


def test_simple_failing_service(app: Flask, client: TestClient) -> None:
    """Test a simple service task that fails immediately."""
    print("\n\nTEST 2: Simple Failing Service Task")
    print("-" * 80)

    # This test uses an existing test BPMN or creates a simple one
    try:
        # Try to use an existing error test
        process_model = load_test_spec(
            process_model_id="test/simple_service_fail",
            bpmn_file_name="test_orphaned_children.bpmn",
            # This would be the simpler BPMN I created above
        )
    except Exception as e:
        print(f"Could not load BPMN: {e}")
        return

    base_test = BaseTest()
    process_instance = base_test.create_process_instance_from_process_model(
        process_model=process_model
    )

    processor = ProcessInstanceProcessor(process_instance)
    try:
        processor.do_engine_steps(save=True)
    except WorkflowExecutionServiceError:
        print("✓ Expected error occurred")

    # Check for orphaned children
    db.session.refresh(process_instance)
    result = OrphanedChildrenChecker.check_for_orphaned_children(process_instance.id)
    OrphanedChildrenChecker.print_report(result)


def check_existing_process_instance(process_instance_id: int) -> None:
    """Check an existing process instance for orphaned children."""
    print(f"\n\nChecking existing process instance: {process_instance_id}")
    print("-" * 80)

    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()
    if not process_instance:
        print(f"✗ Process instance {process_instance_id} not found")
        return

    print(f"Process Model: {process_instance.process_model_identifier}")
    print(f"Status: {process_instance.status}")

    result = OrphanedChildrenChecker.check_for_orphaned_children(process_instance_id)
    OrphanedChildrenChecker.print_report(result)

    # Print task tree
    print("\n\nTask Tree:")
    print("-" * 80)
    tasks = TaskModel.query.filter_by(process_instance_id=process_instance_id).all()
    existing_guids = {t.guid for t in tasks}

    for task in sorted(tasks, key=lambda t: t.id):
        task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"
        children = task.properties_json.get("children", [])
        parent_guid = task.properties_json.get("parent")

        print(f"\n{task_def}")
        print(f"  GUID: {task.guid}")
        print(f"  State: {task.state}")
        if parent_guid:
            parent_exists = parent_guid in existing_guids
            status = "✓" if parent_exists else "✗ MISSING"
            print(f"  Parent: {parent_guid[:8]}... {status}")
        if children:
            print(f"  Children ({len(children)}):")
            for child_guid in children:
                child_exists = child_guid in existing_guids
                status = "✓" if child_exists else "✗ MISSING"
                print(f"    - {child_guid[:8]}... {status}")


if __name__ == "__main__":
    # If run as a script with a process instance ID argument
    if len(sys.argv) > 1:
        try:
            pid = int(sys.argv[1])
            from spiffworkflow_backend import create_app

            app = create_app()
            with app.app_context():
                check_existing_process_instance(pid)
        except ValueError:
            print(f"Invalid process instance ID: {sys.argv[1]}")
            sys.exit(1)
    else:
        print("Usage:")
        print("  python test_orphaned_children_repro.py <process_instance_id>")
        print("\nOr run as a pytest test:")
        print("  pytest test_orphaned_children_repro.py -v")

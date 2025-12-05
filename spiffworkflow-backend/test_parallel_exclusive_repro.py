#!/usr/bin/env python3
"""Test parallel gateway with exclusive gateway after failing service task."""

import pytest
from flask import Flask
from flask.testing import FlaskClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


def test_parallel_gateway_with_exclusive_after_failing_service(
    app: Flask,
    client: FlaskClient,
    with_db_and_bpmn_file_cleanup: None,
) -> None:
    """
    Test the scenario that might trigger orphaned children:

    Parallel Gateway → 3 branches
      Branch A: Simple script task
      Branch B: Service Task (FAILS) → Exclusive Gateway → Multiple routes
      Branch C: Simple script task

    The theory: When the service task fails, SpiffWorkflow may have already
    created PREDICTED children for the exclusive gateway. These get filtered
    out during save, but the parent task may still reference them.
    """
    base_test = BaseTest()

    process_model = load_test_spec(
        process_model_id="test/parallel_exclusive_fail",
        bpmn_file_name="parallel_with_exclusive_fail.bpmn",
        process_model_source_directory="orphaned_children_repro",
    )

    process_instance = base_test.create_process_instance_from_process_model(
        process_model=process_model
    )

    processor = ProcessInstanceProcessor(process_instance)

    print(f"\n{'='*80}")
    print("TESTING: Parallel Gateway → Failing Service Task → Exclusive Gateway")
    print(f"{'='*80}\n")

    # Expect failure
    try:
        processor.do_engine_steps(save=True)
        print("⚠️  Process completed without error (unexpected)")
    except WorkflowExecutionServiceError as e:
        print(f"✓ Process failed as expected")
        print(f"  Error: {str(e)[:150]}...")

    # Refresh and analyze
    db.session.refresh(process_instance)

    all_tasks = TaskModel.query.filter_by(
        process_instance_id=process_instance.id
    ).all()

    existing_guids = {t.guid for t in all_tasks}

    print(f"\n{'='*80}")
    print("TASK ANALYSIS")
    print(f"{'='*80}")
    print(f"\nTotal tasks in database: {len(all_tasks)}")

    # Group by state
    by_state = {}
    for task in all_tasks:
        by_state[task.state] = by_state.get(task.state, 0) + 1

    print("\nTasks by state:")
    for state, count in sorted(by_state.items()):
        print(f"  {state}: {count}")

    # Check for orphaned children
    print(f"\n{'='*80}")
    print("CHECKING FOR ORPHANED CHILDREN")
    print(f"{'='*80}")

    orphaned_found = False
    orphaned_details = []

    for task in all_tasks:
        if "children" not in task.properties_json:
            continue

        children = task.properties_json["children"]
        if not children:
            continue

        task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"

        # Check each child
        missing_children = []
        for child_guid in children:
            if child_guid not in existing_guids:
                missing_children.append(child_guid)

        if missing_children:
            orphaned_found = True
            orphaned_details.append({
                "parent_task": task_def,
                "parent_guid": task.guid,
                "parent_state": task.state,
                "total_children": len(children),
                "missing_children": missing_children,
            })

    if orphaned_found:
        print(f"\n🎉 BUG REPRODUCED! Found {len(orphaned_details)} task(s) with orphaned children!")
        print(f"\n{'='*80}")
        for detail in orphaned_details:
            print(f"\nParent Task: {detail['parent_task']}")
            print(f"  State: {detail['parent_state']}")
            print(f"  GUID: {detail['parent_guid']}")
            print(f"  Total children in JSON: {detail['total_children']}")
            print(f"  Orphaned children: {len(detail['missing_children'])}")
            for missing in detail['missing_children']:
                print(f"    ✗ {missing} (NOT IN DATABASE)")

        # Print detailed task tree
        print(f"\n{'='*80}")
        print("DETAILED TASK TREE")
        print(f"{'='*80}")

        for task in all_tasks:
            task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"
            children = task.properties_json.get("children", [])

            print(f"\n{task_def} [{task.state}]")
            print(f"  GUID: {task.guid}")

            if children:
                print(f"  Children ({len(children)}):")
                for child_guid in children:
                    exists = "✓" if child_guid in existing_guids else "✗ MISSING"
                    child_task = next((t for t in all_tasks if t.guid == child_guid), None)
                    if child_task:
                        child_def = child_task.task_definition.bpmn_identifier if child_task.task_definition else "?"
                        print(f"    {exists} {child_def} ({child_guid[:16]}...)")
                    else:
                        print(f"    {exists} ORPHANED ({child_guid[:16]}...)")

        pytest.fail(
            f"SUCCESS! Reproduced the orphaned children bug. "
            f"Found {len(orphaned_details)} parent task(s) with missing child references."
        )

    else:
        print("\n✅ No orphaned children found")
        print("This scenario did not reproduce the bug")
        print("\nPossible reasons:")
        print("  1. SpiffWorkflow doesn't create PREDICTED tasks in this scenario")
        print("  2. The timing is different than expected")
        print("  3. The bug has been fixed")
        print("  4. We need a different scenario (maybe with subprocesses?)")

        # Still print task tree for analysis
        print(f"\n{'='*80}")
        print("TASK TREE (for analysis)")
        print(f"{'='*80}")

        for task in all_tasks:
            task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"
            children = task.properties_json.get("children", [])

            # Focus on key tasks
            if task_def in ["Task_ServiceFail", "Gateway_Exclusive", "Gateway_Parallel_Fork"]:
                print(f"\n{task_def} [{task.state}]")
                print(f"  GUID: {task.guid[:16]}...")
                if children:
                    print(f"  Children: {len(children)}")
                    for child_guid in children:
                        child_task = next((t for t in all_tasks if t.guid == child_guid), None)
                        if child_task:
                            child_def = child_task.task_definition.bpmn_identifier if child_task.task_definition else "?"
                            print(f"    ✓ {child_def} [{child_task.state}]")


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-xvs"]))

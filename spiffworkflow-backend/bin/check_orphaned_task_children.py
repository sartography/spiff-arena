#!/usr/bin/env python
"""Check for orphaned child task references in a process instance.

This script verifies that all child task references in properties_json["children"]
actually exist in the database. If orphaned references are found, it dumps detailed
information about the broken tasks.

Usage:
    uv run python bin/check_orphaned_task_children.py <process_instance_id>
"""

import json
import sys
from typing import Any

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel


def format_json(data: Any) -> str:
    """Format JSON data for pretty printing."""
    return json.dumps(data, indent=2, default=str)


def dump_task_details(task: TaskModel, label: str) -> None:
    """Print detailed information about a task."""
    print(f"\n{label}")
    print("=" * 80)

    task_def = task.task_definition
    print(f"\nGUID: {task.guid}")
    print(f"State: {task.state}")

    if task_def:
        print(f"BPMN Identifier: {task_def.bpmn_identifier}")
        print(f"BPMN Name: {task_def.bpmn_name}")
        print(f"Type: {task_def.typename}")
    else:
        print("WARNING: No task definition found")

    if task.start_in_seconds:
        print(f"Started: {task.start_in_seconds}")
    if task.end_in_seconds:
        print(f"Ended: {task.end_in_seconds}")

    if task.runtime_info:
        print(f"Runtime Info: {task.runtime_info}")

    print("\nFull Properties JSON:")
    print(format_json(task.properties_json))


def check_process_instance(process_instance_id: int) -> int:
    """Check a process instance for orphaned child references.

    Returns:
        Number of orphaned references found (0 if none)
    """
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()

    if not process_instance:
        print(f"ERROR: Process instance {process_instance_id} not found")
        return 1

    print(f"\nProcess Instance: {process_instance_id}")
    print(f"Process Model: {process_instance.process_model_identifier}")
    print(f"Status: {process_instance.status}")

    all_tasks = TaskModel.query.filter_by(process_instance_id=process_instance_id).all()
    print(f"Total tasks: {len(all_tasks)}")

    existing_task_guids = {task.guid for task in all_tasks}
    task_by_guid = {task.guid: task for task in all_tasks}

    tasks_by_state: dict[str, int] = {}
    for task in all_tasks:
        tasks_by_state[task.state] = tasks_by_state.get(task.state, 0) + 1

    print("\nTasks by state:")
    for state, count in sorted(tasks_by_state.items()):
        print(f"  {state}: {count}")

    print("\n" + "=" * 80)
    print("CHECKING FOR ORPHANED CHILD REFERENCES")
    print("=" * 80)

    orphaned_references_found = []

    for task in all_tasks:
        if "children" not in task.properties_json:
            continue

        children_guids = task.properties_json["children"]
        if not children_guids:
            continue

        # Check each child
        missing_children = []
        for child_guid in children_guids:
            if child_guid not in existing_task_guids:
                missing_children.append(child_guid)

        if missing_children:
            orphaned_references_found.append(
                {
                    "parent_task": task,
                    "missing_children": missing_children,
                    "total_children": len(children_guids),
                }
            )

    if orphaned_references_found:
        print("\nORPHANED REFERENCES FOUND")
        print(f"Tasks with orphaned children: {len(orphaned_references_found)}")
        print(f"Total orphaned references: {sum(len(x['missing_children']) for x in orphaned_references_found)}")

        for idx, orphaned_ref in enumerate(orphaned_references_found, 1):
            parent_task = orphaned_ref["parent_task"]
            missing_children = orphaned_ref["missing_children"]
            task_def = parent_task.task_definition
            task_name = task_def.bpmn_identifier if task_def else "UNKNOWN"

            print(f"\n{'=' * 80}")
            print(f"ORPHANED REFERENCE #{idx}: {task_name}")
            print("=" * 80)
            print(f"Parent GUID: {parent_task.guid}")
            print(f"Parent State: {parent_task.state}")
            print(f"Total children in JSON: {orphaned_ref['total_children']}")
            print(f"Missing children: {len(missing_children)}")

            print("\nMissing child GUIDs:")
            for child_guid in missing_children:
                print(f"  {child_guid}")

            dump_task_details(parent_task, "PARENT TASK DETAILS")

            # Check if these GUIDs exist elsewhere
            for child_guid in missing_children:
                other_task = TaskModel.query.filter_by(guid=child_guid).first()
                if other_task:
                    print(f"\nWARNING: {child_guid} found in different process instance {other_task.process_instance_id}")
                    dump_task_details(other_task, f"MISPLACED TASK: {child_guid}")

            # Show valid children for comparison
            valid_children = [c for c in parent_task.properties_json["children"] if c in existing_task_guids]

            if valid_children:
                print(f"\nValid children of parent ({len(valid_children)}):")
                for child_guid in valid_children:
                    child_task = task_by_guid[child_guid]
                    child_def = child_task.task_definition
                    child_name = child_def.bpmn_identifier if child_def else "UNKNOWN"
                    print(f"  {child_name} [{child_task.state}] - {child_guid}")

        return len(orphaned_references_found)

    else:
        print("\nNO ORPHANED CHILD REFERENCES FOUND")
        print("All child references are valid.")
        return 0


def main(process_instance_id_str: str) -> int:
    """Main entry point."""
    try:
        process_instance_id = int(process_instance_id_str)
    except ValueError:
        print(f"ERROR: Invalid process instance ID: {process_instance_id_str}")
        return 1

    app = create_app()
    with app.app.app_context():
        return check_process_instance(process_instance_id)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./bin/run_local_python_script bin/check_orphaned_task_children.py <process_instance_id>")
        sys.exit(1)

    exit_code = main(sys.argv[1])
    sys.exit(exit_code)

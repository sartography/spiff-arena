#!/usr/bin/env python3
"""
Quick diagnostic script to check a process instance for orphaned child references.

Usage:
    FLASK_APP=src.spiffworkflow_backend python check_orphaned_children.py <process_instance_id>
"""

import sys

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel


def check_orphaned_children(process_instance_id: int) -> None:
    """Check if a process instance has orphaned child references."""
    process_instance = ProcessInstanceModel.query.filter_by(id=process_instance_id).first()

    if not process_instance:
        print(f"ERROR: Process instance {process_instance_id} not found")
        sys.exit(1)

    print(f"\nProcess Instance: {process_instance_id}")
    print(f"Model: {process_instance.process_model_identifier}")
    print(f"Status: {process_instance.status}")
    print("=" * 80)

    # Get all tasks
    tasks = TaskModel.query.filter_by(process_instance_id=process_instance_id).all()
    existing_task_guids = {task.guid for task in tasks}

    print(f"\nTotal tasks in database: {len(tasks)}")
    print(f"\nTask Breakdown by State:")
    state_counts = {}
    for task in tasks:
        state_counts[task.state] = state_counts.get(task.state, 0) + 1
    for state, count in sorted(state_counts.items()):
        print(f"  {state}: {count}")

    # Check for orphaned references
    print("\n" + "=" * 80)
    print("CHECKING FOR ORPHANED CHILD REFERENCES...")
    print("=" * 80)

    orphaned_found = False
    for task in tasks:
        if "children" not in task.properties_json:
            continue

        children_guids = task.properties_json["children"]
        if not children_guids:
            continue

        task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"

        # Check each child
        missing_children = []
        for child_guid in children_guids:
            if child_guid not in existing_task_guids:
                missing_children.append(child_guid)

        if missing_children:
            orphaned_found = True
            print(f"\n⚠️  ORPHANED CHILDREN FOUND!")
            print(f"    Parent Task: {task_def}")
            print(f"    Parent GUID: {task.guid}")
            print(f"    Parent State: {task.state}")
            print(f"    Total Children in properties_json: {len(children_guids)}")
            print(f"    Missing Children: {len(missing_children)}")
            for child_guid in missing_children:
                print(f"      - {child_guid} (NOT IN DATABASE)")

    if not orphaned_found:
        print("\n✅ No orphaned child references found!")
        print("All child references exist in the database.")
    else:
        print("\n" + "=" * 80)
        print("🐛 BUG CONFIRMED: Orphaned child references found!")
        print("=" * 80)

    # Print full task tree for debugging
    print("\n" + "=" * 80)
    print("FULL TASK TREE:")
    print("=" * 80)

    # Group tasks by parent
    tasks_by_parent = {}
    root_tasks = []

    for task in tasks:
        parent_guid = task.properties_json.get("parent")
        if parent_guid is None:
            root_tasks.append(task)
        else:
            if parent_guid not in tasks_by_parent:
                tasks_by_parent[parent_guid] = []
            tasks_by_parent[parent_guid].append(task)

    def print_task_tree(task, indent=0):
        """Recursively print task tree."""
        task_def = task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN"
        prefix = "  " * indent
        print(f"{prefix}├─ {task_def}")
        print(f"{prefix}   GUID: {task.guid[:8]}...")
        print(f"{prefix}   State: {task.state}")

        # Check if this task has children
        children_in_json = task.properties_json.get("children", [])
        if children_in_json:
            print(f"{prefix}   Children in JSON: {len(children_in_json)}")
            for child_guid in children_in_json:
                child_exists = child_guid in existing_task_guids
                if not child_exists:
                    print(f"{prefix}     ✗ {child_guid[:8]}... (ORPHANED - NOT IN DB)")
                else:
                    # Find and print the child
                    child_task = next((t for t in tasks if t.guid == child_guid), None)
                    if child_task:
                        print_task_tree(child_task, indent + 2)

    for root_task in root_tasks:
        print_task_tree(root_task)

    print("\n" + "=" * 80)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: FLASK_APP=src.spiffworkflow_backend python check_orphaned_children.py <process_instance_id>")
        sys.exit(1)

    try:
        process_instance_id = int(sys.argv[1])
    except ValueError:
        print(f"ERROR: Invalid process instance ID: {sys.argv[1]}")
        sys.exit(1)

    app = create_app()
    with app.app.app_context():
        check_orphaned_children(process_instance_id)

#!/usr/bin/env python
"""Check ALL process instances for orphaned child task references.

This script scans all process instances in the database and reports which ones
have orphaned child references. Useful for finding the extent of the issue.

Usage:
    ./bin/run_local_python_script bin/check_all_process_instances_for_orphaned_children.py [--limit N] [--status STATUS]

Options:
    --limit N        Only check the first N process instances (default: all)
    --status STATUS  Only check process instances with this status (e.g., error, complete)
"""

import sys
from typing import Any

from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel


def check_all_process_instances(limit: int | None = None, status_filter: str | None = None) -> dict[str, Any]:
    """Check all process instances for orphaned child references.

    Returns:
        Dictionary with summary statistics
    """
    # Query process instances
    query = ProcessInstanceModel.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if limit:
        query = query.limit(limit)

    process_instances = query.all()

    print(f"\n{'='*80}")
    print(f"CHECKING {len(process_instances)} PROCESS INSTANCE(S) FOR ORPHANED CHILDREN")
    if status_filter:
        print(f"Status Filter: {status_filter}")
    print(f"{'='*80}\n")

    affected_process_instances = []
    total_orphaned_references = 0
    total_tasks_checked = 0

    for idx, process_instance in enumerate(process_instances, 1):
        # Get all tasks for this process instance
        all_tasks = TaskModel.query.filter_by(process_instance_id=process_instance.id).all()
        total_tasks_checked += len(all_tasks)

        # Build set of existing task GUIDs
        existing_task_guids = {task.guid for task in all_tasks}

        # Check for orphaned children
        orphaned_count = 0
        tasks_with_orphaned_children = []

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
                orphaned_count += len(missing_children)
                tasks_with_orphaned_children.append({
                    "task_guid": task.guid,
                    "task_state": task.state,
                    "task_bpmn_id": task.task_definition.bpmn_identifier if task.task_definition else "UNKNOWN",
                    "missing_count": len(missing_children),
                })

        if orphaned_count > 0:
            affected_process_instances.append({
                "process_instance_id": process_instance.id,
                "process_model": process_instance.process_model_identifier,
                "status": process_instance.status,
                "orphaned_references": orphaned_count,
                "tasks_with_orphans": len(tasks_with_orphaned_children),
                "task_details": tasks_with_orphaned_children,
            })
            total_orphaned_references += orphaned_count

        # Progress indicator
        if idx % 100 == 0:
            print(f"Checked {idx}/{len(process_instances)} process instances...")

    # Print summary
    print(f"\n{'='*80}")
    print("SCAN COMPLETE")
    print(f"{'='*80}\n")

    print(f"Total Process Instances Scanned: {len(process_instances)}")
    print(f"Total Tasks Checked: {total_tasks_checked}")
    print(f"Process Instances with Orphaned References: {len(affected_process_instances)}")
    print(f"Total Orphaned Child References: {total_orphaned_references}")

    if affected_process_instances:
        print(f"\n{'='*80}")
        print("AFFECTED PROCESS INSTANCES")
        print(f"{'='*80}\n")

        print(f"{'Process ID':<12} {'Status':<12} {'Model':<40} {'Orphans':<10} {'Tasks':<10}")
        print(f"{'-'*12} {'-'*12} {'-'*40} {'-'*10} {'-'*10}")

        for item in affected_process_instances:
            model = item['process_model']
            if len(model) > 37:
                model = model[:34] + "..."

            print(
                f"{item['process_instance_id']:<12} "
                f"{item['status']:<12} "
                f"{model:<40} "
                f"{item['orphaned_references']:<10} "
                f"{item['tasks_with_orphans']:<10}"
            )

        print(f"\n{'='*80}")
        print("DETAILED BREAKDOWN")
        print(f"{'='*80}\n")

        for item in affected_process_instances:
            print(f"\nProcess Instance: {item['process_instance_id']}")
            print(f"  Model: {item['process_model']}")
            print(f"  Status: {item['status']}")
            print(f"  Total Orphaned References: {item['orphaned_references']}")
            print(f"  Tasks with Orphaned Children:")

            for task_detail in item['task_details']:
                print(f"    - {task_detail['task_bpmn_id']} [{task_detail['task_state']}]")
                print(f"      GUID: {task_detail['task_guid']}")
                print(f"      Missing Children: {task_detail['missing_count']}")

        print(f"\n{'='*80}")
        print("RECOMMENDATIONS")
        print(f"{'='*80}\n")

        print("To get detailed information about a specific process instance, run:")
        print(f"  ./bin/run_local_python_script bin/check_orphaned_task_children.py <process_instance_id>")
        print("\nExample:")
        print(f"  ./bin/run_local_python_script bin/check_orphaned_task_children.py {affected_process_instances[0]['process_instance_id']}")

    else:
        print("\n✅ NO ORPHANED CHILD REFERENCES FOUND")
        print("\nAll process instances have valid child task references!")

    return {
        "total_checked": len(process_instances),
        "total_tasks": total_tasks_checked,
        "affected_count": len(affected_process_instances),
        "total_orphans": total_orphaned_references,
        "affected_instances": affected_process_instances,
    }


def main(args: list[str]) -> int:
    """Main entry point."""
    limit = None
    status_filter = None

    # Parse arguments
    i = 0
    while i < len(args):
        if args[i] == "--limit" and i + 1 < len(args):
            try:
                limit = int(args[i + 1])
                i += 2
            except ValueError:
                print(f"❌ ERROR: Invalid limit value: {args[i + 1]}")
                return 1
        elif args[i] == "--status" and i + 1 < len(args):
            status_filter = args[i + 1]
            i += 2
        else:
            print(f"❌ ERROR: Unknown argument: {args[i]}")
            print("\nUsage: check_all_process_instances_for_orphaned_children.py [--limit N] [--status STATUS]")
            return 1

    app = create_app()
    with app.app.app_context():
        result = check_all_process_instances(limit=limit, status_filter=status_filter)

        # Return non-zero if orphans found
        return 1 if result["affected_count"] > 0 else 0


if __name__ == "__main__":
    exit_code = main(sys.argv[1:])
    sys.exit(exit_code)

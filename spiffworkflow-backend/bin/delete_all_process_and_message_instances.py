#!/usr/bin/env python3

"""Delete all process instances and message instances from the database.

This script will:
1. Delete all standalone message instances (not tied to a process instance)
2. Delete all process instances (which cascades to delete associated message instances and related data)

WARNING: This is a destructive operation that cannot be undone!
"""

import os
import sys

# Add the src directory to the Python path so we can import spiffworkflow_backend
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, "src")
sys.path.insert(0, src_dir)

# Import after path modification
# ruff: noqa: E402
from spiffworkflow_backend import create_app
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


def show_counts():
    """Show counts of instances before deletion."""
    print("WARNING: This will delete ALL process instances and message instances!")
    print("This operation is IRREVERSIBLE and will remove all workflow data.")
    print()

    # Get counts first
    app = create_app()
    with app.app.app_context():
        process_instance_count = db.session.query(ProcessInstanceModel).count()
        message_instance_count = db.session.query(MessageInstanceModel).count()
        standalone_message_count = (
            db.session.query(MessageInstanceModel).filter(MessageInstanceModel.process_instance_id.is_(None)).count()
        )

    print("Found:")
    print(f"  - {process_instance_count} process instances")
    print(f"  - {message_instance_count} total message instances")
    print(f"  - {standalone_message_count} standalone message instances")
    print()


def delete_all_instances():
    """Delete all process instances and message instances."""
    app = create_app()
    with app.app.app_context():
        print("Starting deletion process...")

        # Step 1: Delete standalone message instances (not tied to a process instance)
        print("Deleting standalone message instances...")
        standalone_messages = db.session.query(MessageInstanceModel).filter(MessageInstanceModel.process_instance_id.is_(None))
        standalone_count = standalone_messages.count()
        standalone_messages.delete(synchronize_session=False)
        print(f"Deleted {standalone_count} standalone message instances")

        # Step 2: Delete all process instances (cascades to delete associated data)
        print("Deleting process instances...")

        # Process in batches to avoid memory issues with large datasets
        batch_size = 100
        total_deleted = 0

        while True:
            # Get a batch of process instances
            batch = db.session.query(ProcessInstanceModel).limit(batch_size).all()

            if not batch:
                break  # No more instances to delete

            # Delete this batch
            for instance in batch:
                db.session.delete(instance)

            batch_count = len(batch)
            total_deleted += batch_count
            print(f"Deleting batch of {batch_count} process instances... (total: {total_deleted})")

            # Commit this batch
            db.session.commit()

            # If we got less than batch_size, we're done
            if batch_count < batch_size:
                break

        print(f"Successfully deleted {total_deleted} process instances and all associated data")
        print()

        # Verify counts
        remaining_processes = db.session.query(ProcessInstanceModel).count()
        remaining_messages = db.session.query(MessageInstanceModel).count()

        print("Verification:")
        print(f"  - {remaining_processes} process instances remaining")
        print(f"  - {remaining_messages} message instances remaining")

        if remaining_processes == 0 and remaining_messages == 0:
            print("✓ All process instances and message instances have been deleted successfully!")
        else:
            print("⚠ Some instances may still remain - check for any constraints or issues")


def main():
    """Main function."""
    show_counts()

    try:
        delete_all_instances()
    except Exception as e:
        print(f"Error during deletion: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

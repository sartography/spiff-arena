"""Validate the task GUID foreign keys after their low-lock rebind.

Revision ID: da1b93ec3bc2
Revises: 7ae9aa325816
Create Date: 2026-07-29 16:32:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "da1b93ec3bc2"
down_revision = "7ae9aa325816"
branch_labels = None
depends_on = None


def upgrade():
    if op.get_bind().dialect.name != "postgresql":
        return

    # Entering the autocommit block commits the preceding revision's brief
    # constraint-swap transaction before validation scans future_task. The
    # validation locks permit normal reads and writes.
    with op.get_context().autocommit_block():
        op.execute(
            "ALTER TABLE future_task "
            "VALIDATE CONSTRAINT future_task_task_guid_fk"
        )
        op.execute(
            "ALTER TABLE human_task "
            "VALIDATE CONSTRAINT human_task_ibfk_task_guid"
        )


def downgrade():
    # A validated foreign key is compatible with the preceding revision's
    # NOT VALID declaration and remains safe to keep validated.
    pass

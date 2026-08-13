"""Drop the redundant explicit task GUID index.

Revision ID: 06c63b723d1e
Revises: d9d54e36c69f
Create Date: 2026-07-29 16:30:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "06c63b723d1e"
down_revision = "d9d54e36c69f"
branch_labels = None
depends_on = None


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        # The primary key already provides the same unique btree lookup.
        # Autocommit is required by PostgreSQL for concurrent index changes.
        with op.get_context().autocommit_block():
            op.execute("DROP INDEX CONCURRENTLY IF EXISTS ix_task_guid")
    elif dialect == "mysql":
        op.execute(
            "ALTER TABLE task DROP INDEX ix_task_guid, "
            "ALGORITHM=INPLACE, LOCK=NONE"
        )
    else:
        with op.batch_alter_table("task", schema=None) as batch_op:
            batch_op.drop_index("ix_task_guid")


def downgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        with op.get_context().autocommit_block():
            # A full downgrade reaches this revision after restoring the
            # historical unique constraint and rebinding these foreign keys as
            # NOT VALID. Committing and validating here avoids holding the
            # short constraint-swap locks during either validation scan.
            op.execute(
                "ALTER TABLE future_task "
                "VALIDATE CONSTRAINT future_task_task_guid_fk"
            )
            op.execute(
                "ALTER TABLE human_task "
                "VALIDATE CONSTRAINT human_task_ibfk_task_guid"
            )
            op.execute(
                "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS "
                "ix_task_guid ON task (guid)"
            )
    elif dialect == "mysql":
        op.execute(
            "ALTER TABLE task ADD UNIQUE INDEX ix_task_guid (guid), "
            "ALGORITHM=INPLACE, LOCK=NONE"
        )
    else:
        with op.batch_alter_table("task", schema=None) as batch_op:
            batch_op.create_index("ix_task_guid", ["guid"], unique=True)

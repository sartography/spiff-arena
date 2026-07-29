"""Rebind task GUID foreign keys to the primary key.

Revision ID: 7ae9aa325816
Revises: 06c63b723d1e
Create Date: 2026-07-29 16:31:00.000000

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "7ae9aa325816"
down_revision = "06c63b723d1e"
branch_labels = None
depends_on = None


FUTURE_TASK_FK = "future_task_task_guid_fk"
HUMAN_TASK_FK = "human_task_ibfk_task_guid"


def _set_postgresql_metadata_timeouts():
    op.execute("SET LOCAL lock_timeout = '5s'")
    op.execute("SET LOCAL statement_timeout = '30s'")


def _drop_task_foreign_keys():
    with op.batch_alter_table("future_task", schema=None) as batch_op:
        batch_op.drop_constraint(FUTURE_TASK_FK, type_="foreignkey")
    with op.batch_alter_table("human_task", schema=None) as batch_op:
        batch_op.drop_constraint(HUMAN_TASK_FK, type_="foreignkey")


def _create_task_foreign_keys(*, not_valid=False):
    postgresql_options = {"postgresql_not_valid": True} if not_valid else {}
    with op.batch_alter_table("future_task", schema=None) as batch_op:
        batch_op.create_foreign_key(
            FUTURE_TASK_FK,
            "task",
            ["guid"],
            ["guid"],
            ondelete="CASCADE",
            **postgresql_options,
        )
    with op.batch_alter_table("human_task", schema=None) as batch_op:
        batch_op.create_foreign_key(
            HUMAN_TASK_FK,
            "task",
            ["task_guid"],
            ["guid"],
            **postgresql_options,
        )


def upgrade():
    dialect = op.get_bind().dialect.name
    # Migration 3191627ae224 removed MySQL's historical `guid` unique index
    # before it added the primary key. Only PostgreSQL and SQLite retained the
    # separate constraint that this revision removes.
    if dialect == "mysql":
        return

    if dialect == "postgresql":
        _set_postgresql_metadata_timeouts()
    _drop_task_foreign_keys()
    with op.batch_alter_table("task", schema=None) as batch_op:
        batch_op.drop_constraint("guid", type_="unique")
    _create_task_foreign_keys(not_valid=dialect == "postgresql")


def downgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "mysql":
        return

    if dialect == "postgresql":
        # Build the large replacement index without blocking task reads/writes,
        # then attach it to the restored unique constraint in the short
        # metadata-only transaction below.
        with op.get_context().autocommit_block():
            op.execute(
                "CREATE UNIQUE INDEX CONCURRENTLY IF NOT EXISTS guid ON task (guid)"
            )

        _set_postgresql_metadata_timeouts()
        _drop_task_foreign_keys()
        op.execute(
            "ALTER TABLE task ADD CONSTRAINT guid UNIQUE USING INDEX guid"
        )
        _create_task_foreign_keys(not_valid=True)
    else:
        _drop_task_foreign_keys()
        with op.batch_alter_table("task", schema=None) as batch_op:
            batch_op.create_unique_constraint("guid", ["guid"])
        _create_task_foreign_keys()

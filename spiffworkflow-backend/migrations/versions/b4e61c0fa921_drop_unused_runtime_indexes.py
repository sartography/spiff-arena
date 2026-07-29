"""Drop unused runtime indexes.

Revision ID: b4e61c0fa921
Revises: da1b93ec3bc2
Create Date: 2026-07-29 20:30:00.000000

"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "b4e61c0fa921"
down_revision = "da1b93ec3bc2"
branch_labels = None
depends_on = None


INDEXES_BY_TABLE = {
    "bpmn_process": ("ix_bpmn_process_json_data_hash",),
    "process_instance_event": (
        "ix_process_instance_event_event_type",
        "ix_process_instance_event_timestamp",
    ),
    "task": (
        "ix_task_json_data_hash",
        "ix_task_python_env_data_hash",
        "ix_task_state",
    ),
}


def upgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        with op.get_context().autocommit_block():
            for indexes in INDEXES_BY_TABLE.values():
                for index_name in indexes:
                    op.execute(f"DROP INDEX CONCURRENTLY IF EXISTS {index_name}")
    elif dialect == "mysql":
        for table, indexes in INDEXES_BY_TABLE.items():
            drops = ", ".join(f"DROP INDEX {index_name}" for index_name in indexes)
            op.execute(f"ALTER TABLE {table} {drops}, ALGORITHM=INPLACE, LOCK=NONE")
    else:
        for table, indexes in INDEXES_BY_TABLE.items():
            with op.batch_alter_table(table, schema=None) as batch_op:
                for index_name in indexes:
                    batch_op.drop_index(index_name)


def downgrade():
    dialect = op.get_bind().dialect.name
    if dialect == "postgresql":
        with op.get_context().autocommit_block():
            for table, indexes in INDEXES_BY_TABLE.items():
                for index_name in indexes:
                    column = index_name.removeprefix(f"ix_{table}_")
                    op.execute(f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table} ({column})")
    elif dialect == "mysql":
        for table, indexes in INDEXES_BY_TABLE.items():
            additions = ", ".join(f"ADD INDEX {index_name} ({index_name.removeprefix(f'ix_{table}_')})" for index_name in indexes)
            op.execute(f"ALTER TABLE {table} {additions}, ALGORITHM=INPLACE, LOCK=NONE")
    else:
        for table, indexes in INDEXES_BY_TABLE.items():
            with op.batch_alter_table(table, schema=None) as batch_op:
                for index_name in indexes:
                    column = index_name.removeprefix(f"ix_{table}_")
                    batch_op.create_index(index_name, [column], unique=False)

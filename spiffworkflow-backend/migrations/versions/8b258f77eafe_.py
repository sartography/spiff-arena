"""empty message

Revision ID: 8b258f77eafe
Revises: 4efc3d8655be
Create Date: 2026-01-12 16:59:26.261161

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = "8b258f77eafe"
down_revision = "4efc3d8655be"
branch_labels = None
depends_on = None

# It would be safer to migrate the draft data
# That is unfortunately non-trivial.
def delete_task_draft_data():
    conn = op.get_bind()

    delete_query = text("""
        DELETE FROM task_draft_data;
    """)

    conn.execute(delete_query)


def upgrade():
    delete_task_draft_data()
    with op.batch_alter_table("task_draft_data", schema=None) as batch_op:
        batch_op.add_column(sa.Column("task_guid", sa.String(length=36), nullable=False))
        batch_op.drop_constraint("process_instance_task_definition_pk", type_="primary")
        batch_op.drop_constraint("process_instance_task_definition_unique", type_="unique")


        batch_op.create_unique_constraint(
            "process_instance_task_unique", ["process_instance_id", "task_guid"]
        )
        batch_op.create_primary_key(
            "process_instance_task_pk", ["process_instance_id", "task_guid"]
        )

        batch_op.drop_index("ix_task_draft_data_task_definition_id_path")
        batch_op.create_index("ix_task_draft_data_task_guid", ["task_guid"], unique=False)

        batch_op.create_foreign_key("task_draft_data_task_guid_fk", "task", ["task_guid"], ["guid"])
        batch_op.drop_column("task_definition_id_path")


def downgrade():
    delete_task_draft_data()
    with op.batch_alter_table("task_draft_data", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "task_definition_id_path", mysql.VARCHAR(length=255), nullable=False
            )
        )
        batch_op.drop_constraint(None, type_="foreignkey")
        batch_op.drop_constraint("process_instance_task_unique", type_="unique")
        batch_op.drop_index(batch_op.f("ix_task_draft_data_task_guid"))
        batch_op.create_unique_constraint(
            batch_op.f("process_instance_task_definition_unique"),
            ["process_instance_id", "task_definition_id_path"],
        )
        batch_op.create_index(
            batch_op.f("ix_task_draft_data_task_definition_id_path"),
            ["task_definition_id_path"],
            unique=False,
        )
        batch_op.drop_column("task_guid")


"""preserve instruction render context

Revision ID: d6f2a9b47c31
Revises: c8d7e4a91f2b
Create Date: 2026-08-30 09:15:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d6f2a9b47c31"
down_revision = "c8d7e4a91f2b"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("task_instructions_for_end_user", schema=None) as batch_op:
        batch_op.add_column(sa.Column("instruction_template", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("task_data", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("process_model_identifier", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("bpmn_file_name", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("bpmn_process_identifier", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("task_bpmn_identifier", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("source_artifact_ref", sa.JSON(), nullable=True))
        batch_op.add_column(sa.Column("bpmn_version_control_identifier", sa.String(length=255), nullable=True))


def downgrade():
    with op.batch_alter_table("task_instructions_for_end_user", schema=None) as batch_op:
        batch_op.drop_column("bpmn_version_control_identifier")
        batch_op.drop_column("source_artifact_ref")
        batch_op.drop_column("task_bpmn_identifier")
        batch_op.drop_column("bpmn_process_identifier")
        batch_op.drop_column("bpmn_file_name")
        batch_op.drop_column("process_model_identifier")
        batch_op.drop_column("task_data")
        batch_op.drop_column("instruction_template")

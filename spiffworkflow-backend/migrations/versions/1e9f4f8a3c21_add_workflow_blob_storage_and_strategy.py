"""add workflow blob storage and per-instance strategy

Revision ID: 1e9f4f8a3c21
Revises: 52f3e86566bf
Create Date: 2026-03-06 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1e9f4f8a3c21'
down_revision = '52f3e86566bf'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('process_instance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('workflow_storage_strategy', sa.String(length=50), nullable=True))
        batch_op.create_index(batch_op.f('ix_process_instance_workflow_storage_strategy'), ['workflow_storage_strategy'], unique=False)

    op.create_table(
        'workflow_blob_storage',
        sa.Column('process_instance_id', sa.Integer(), nullable=False),
        sa.Column('workflow_data', sa.JSON(), nullable=False),
        sa.Column('serializer_version', sa.String(length=50), nullable=True),
        sa.Column('created_at_in_seconds', sa.Integer(), nullable=False),
        sa.Column('updated_at_in_seconds', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['process_instance_id'], ['process_instance.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('process_instance_id')
    )


def downgrade():
    op.drop_table('workflow_blob_storage')

    with op.batch_alter_table('process_instance', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_process_instance_workflow_storage_strategy'))
        batch_op.drop_column('workflow_storage_strategy')

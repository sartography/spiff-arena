"""add json_metadata to human_task

Revision ID: 88188256d1a5
Revises: efa7a9f771a6
Create Date: 2025-11-19 22:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '88188256d1a5'
down_revision = 'efa7a9f771a6'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('human_task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('json_metadata', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('human_task', schema=None) as batch_op:
        batch_op.drop_column('json_metadata')

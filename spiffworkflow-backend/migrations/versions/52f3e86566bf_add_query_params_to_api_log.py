"""add query_params to api_log table

Revision ID: 52f3e86566bf
Revises: ffef09e6ddf1
Create Date: 2025-12-13 12:25:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52f3e86566bf'
down_revision = '4efc3d8655be'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('api_log', schema=None) as batch_op:
        batch_op.add_column(sa.Column('query_params', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('api_log', schema=None) as batch_op:
        batch_op.drop_column('query_params')

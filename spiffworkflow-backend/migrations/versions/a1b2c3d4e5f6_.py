"""Add process_model_identifiers to message table

Revision ID: a1b2c3d4e5f6
Revises: 0b90171055cd
Create Date: 2026-04-07 16:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '0b90171055cd'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.add_column(sa.Column('process_model_identifiers', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('message', schema=None) as batch_op:
        batch_op.drop_column('process_model_identifiers')

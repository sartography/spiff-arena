"""empty message

Revision ID: ffef09e6ddf1
Revises: fc5815a9d482
Create Date: 2024-06-26 14:22:42.317828

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffef09e6ddf1'
down_revision = 'fc5815a9d482'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('process_instance', schema=None) as batch_op:
        batch_op.add_column(sa.Column('summary', sa.String(length=255), nullable=True))
        batch_op.create_index(batch_op.f('ix_process_instance_summary'), ['summary'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('process_instance', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_process_instance_summary'))
        batch_op.drop_column('summary')

    # ### end Alembic commands ###

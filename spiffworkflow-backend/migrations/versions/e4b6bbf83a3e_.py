"""empty message

Revision ID: e4b6bbf83a3e
Revises: 6aa02463da9c
Create Date: 2023-05-30 10:17:10.595965

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'e4b6bbf83a3e'
down_revision = '6aa02463da9c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('process_model_cycle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('process_model_identifier', sa.String(length=255), nullable=False),
    sa.Column('cycle_count', sa.Integer(), nullable=True),
    sa.Column('duration_in_seconds', sa.Integer(), nullable=True),
    sa.Column('current_cycle', sa.Integer(), nullable=True),
    sa.Column('updated_at_in_seconds', sa.Integer(), nullable=True),
    sa.Column('created_at_in_seconds', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('process_model_cycle', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_process_model_cycle_process_model_identifier'), ['process_model_identifier'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('process_model_cycle', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_process_model_cycle_process_model_identifier'))

    op.drop_table('process_model_cycle')
    # ### end Alembic commands ###

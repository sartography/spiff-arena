"""empty message

Revision ID: bc2b84d013e0
Revises: 3191627ae224
Create Date: 2024-01-03 13:06:57.981736

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'bc2b84d013e0'
down_revision = '3191627ae224'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('process_instance_file_data', schema=None) as batch_op:
        batch_op.drop_column('identifier')
        batch_op.drop_column('list_index')

    # originally changed in 3191627ae224 but not as a unique key. this will make it unique
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_index('ix_task_guid')
        batch_op.create_index(batch_op.f('ix_task_guid'), ['guid'], unique=True)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task_guid'))
        batch_op.create_index('ix_task_guid', ['guid'], unique=False)

    with op.batch_alter_table('process_instance_file_data', schema=None) as batch_op:
        batch_op.add_column(sa.Column('list_index', mysql.INTEGER(), autoincrement=False, nullable=True))
        batch_op.add_column(sa.Column('identifier', mysql.VARCHAR(length=255), nullable=False))

    # ### end Alembic commands ###

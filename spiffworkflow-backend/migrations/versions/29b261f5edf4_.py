"""empty message

Revision ID: 29b261f5edf4
Revises: 343b406f723d
Create Date: 2024-02-06 13:52:18.973974

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '29b261f5edf4'
down_revision = '343b406f723d'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('future_task', schema=None) as batch_op:
        batch_op.add_column(sa.Column('archived_for_process_instance_status', sa.Boolean(), server_default=sa.text('false'), nullable=False))
        batch_op.create_index(batch_op.f('ix_future_task_archived_for_process_instance_status'), ['archived_for_process_instance_status'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('future_task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_future_task_archived_for_process_instance_status'))
        batch_op.drop_column('archived_for_process_instance_status')

    # ### end Alembic commands ###

"""Add source_is_open_id to group and added_by to human_task_user

Revision ID: f318f9f1b110
Revises: ac125644907a
Create Date: 2024-07-29 15:36:43.230973

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f318f9f1b110'
down_revision = 'ac125644907a'
branch_labels = None
depends_on = None


def upgrade():
    # Adiciona a coluna 'source_is_open_id' na tabela 'group' como nullable e atualiza valores
    with op.batch_alter_table('group', schema=None) as batch_op:
        batch_op.add_column(sa.Column('source_is_open_id', sa.Boolean(), nullable=True))

    # Define um valor padrão para 'source_is_open_id' onde for NULL
    op.execute('UPDATE "group" SET source_is_open_id = FALSE WHERE source_is_open_id IS NULL')

    # Altera a coluna para ser NOT NULL
    with op.batch_alter_table('group', schema=None) as batch_op:
        batch_op.alter_column('source_is_open_id', nullable=False)

        batch_op.create_index(batch_op.f('ix_group_source_is_open_id'), ['source_is_open_id'], unique=False)

    # Adiciona a coluna 'added_by' na tabela 'human_task_user'
    with op.batch_alter_table('human_task_user', schema=None) as batch_op:
        batch_op.add_column(sa.Column('added_by', sa.String(length=50), nullable=True))
        batch_op.create_index(batch_op.f('ix_human_task_user_added_by'), ['added_by'], unique=False)


def downgrade():
    # Remove as mudanças na tabela 'human_task_user'
    with op.batch_alter_table('human_task_user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_human_task_user_added_by'))
        batch_op.drop_column('added_by')

    # Remove as mudanças na tabela 'group'
    with op.batch_alter_table('group', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_group_source_is_open_id'))
        batch_op.drop_column('source_is_open_id')

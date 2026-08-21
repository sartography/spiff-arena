"""add ix_bpmn_process_definition_single_process_hash

Revision ID: 9a2f1c8b7d3e
Revises: d9d54e36c69f
Create Date: 2026-08-21 12:00:00.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '9a2f1c8b7d3e'
down_revision = 'd9d54e36c69f'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('bpmn_process_definition', schema=None) as batch_op:
        batch_op.create_index(
            batch_op.f('ix_bpmn_process_definition_single_process_hash'),
            ['single_process_hash'],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table('bpmn_process_definition', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_bpmn_process_definition_single_process_hash'))

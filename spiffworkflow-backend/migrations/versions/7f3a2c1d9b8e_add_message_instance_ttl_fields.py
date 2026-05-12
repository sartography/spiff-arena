"""add message instance ttl fields

Revision ID: 7f3a2c1d9b8e
Revises: 0b90171055cd
Create Date: 2026-05-12 15:36:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "7f3a2c1d9b8e"
down_revision = "0b90171055cd"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("message_instance", schema=None) as batch_op:
        batch_op.add_column(sa.Column("message_instance_uuid", sa.String(length=40), nullable=True))
        batch_op.add_column(sa.Column("expires_at_in_seconds", sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f("ix_message_instance_message_instance_uuid"),
            ["message_instance_uuid"],
            unique=True,
        )
        batch_op.create_index(batch_op.f("ix_message_instance_expires_at_in_seconds"), ["expires_at_in_seconds"], unique=False)


def downgrade():
    with op.batch_alter_table("message_instance", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_message_instance_expires_at_in_seconds"))
        batch_op.drop_index(batch_op.f("ix_message_instance_message_instance_uuid"))
        batch_op.drop_column("expires_at_in_seconds")
        batch_op.drop_column("message_instance_uuid")

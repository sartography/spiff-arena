"""add source artifact reference to process instance

Revision ID: c8d7e4a91f2b
Revises: 2d68edd689b9
Create Date: 2026-08-30 09:05:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c8d7e4a91f2b"
down_revision = "2d68edd689b9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("process_instance", schema=None) as batch_op:
        batch_op.add_column(sa.Column("source_artifact_ref", sa.JSON(), nullable=True))

def downgrade():
    with op.batch_alter_table("process_instance", schema=None) as batch_op:
        batch_op.drop_column("source_artifact_ref")

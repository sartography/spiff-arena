"""merge task assignment and blob heads

Revision ID: 2c5b1d4a7e8f
Revises: 0b90171055cd, 9a53b7f0d2c1
Create Date: 2026-03-17 17:09:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2c5b1d4a7e8f"
down_revision = ("0b90171055cd", "9a53b7f0d2c1")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

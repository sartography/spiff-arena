"""merge task assignment and api log heads

Revision ID: 9f0d2a6b3c4e
Revises: 0b90171055cd, 52f3e86566bf
Create Date: 2026-03-06 03:35:00.000000
"""

from collections.abc import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "9f0d2a6b3c4e"
down_revision: str | Sequence[str] | None = ("0b90171055cd", "52f3e86566bf")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass

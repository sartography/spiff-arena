"""merging two heads

Revision ID: 1073364bc015
Revises: 214e0c5fb418, 5c50ecf2c1cd, ebf5e733d109
Create Date: 2023-08-21 13:22:36.060366

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1073364bc015'
down_revision = ('214e0c5fb418', '5c50ecf2c1cd', 'ebf5e733d109')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

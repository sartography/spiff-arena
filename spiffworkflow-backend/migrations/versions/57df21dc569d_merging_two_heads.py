"""merging two heads

Revision ID: 57df21dc569d
Revises: 5579975401dd, f04cbd9f43ec
Create Date: 2023-09-07 13:54:23.061873

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '57df21dc569d'
down_revision = ('5579975401dd', 'f04cbd9f43ec')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

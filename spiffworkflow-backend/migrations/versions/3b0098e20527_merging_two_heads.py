"""merging two heads

Revision ID: 3b0098e20527
Revises: 349b48184dfe, f04cbd9f43ec
Create Date: 2023-09-07 11:24:10.914807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b0098e20527'
down_revision = ('349b48184dfe', 'f04cbd9f43ec')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass

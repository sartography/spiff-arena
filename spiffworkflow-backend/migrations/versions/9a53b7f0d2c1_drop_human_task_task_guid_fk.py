"""drop human_task task_guid foreign key for blob storage compatibility

Revision ID: 9a53b7f0d2c1
Revises: 1e9f4f8a3c21
Create Date: 2026-03-07 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "9a53b7f0d2c1"
down_revision = "1e9f4f8a3c21"
branch_labels = None
depends_on = None


def _task_guid_fk_name() -> str | None:
    inspector = sa.inspect(op.get_bind())
    for fk in inspector.get_foreign_keys("human_task"):
        constrained_columns = fk.get("constrained_columns") or []
        referred_table = fk.get("referred_table")
        if constrained_columns == ["task_guid"] and referred_table == "task":
            return fk.get("name")
    return None


def upgrade() -> None:
    fk_name = _task_guid_fk_name()
    if fk_name:
        with op.batch_alter_table("human_task", schema=None) as batch_op:
            batch_op.drop_constraint(fk_name, type_="foreignkey")


def downgrade() -> None:
    fk_name = _task_guid_fk_name()
    if fk_name:
        return

    with op.batch_alter_table("human_task", schema=None) as batch_op:
        batch_op.create_foreign_key("human_task_ibfk_task_guid", "task", ["task_guid"], ["guid"])

"""Preserve immutable model source files independently of compiled definitions.

Revision ID: 82efc719a603
Revises: 2d68edd689b9
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql import LONGBLOB

revision = "82efc719a603"
down_revision = "2d68edd689b9"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "model_source_blob",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("contents", sa.LargeBinary().with_variant(LONGBLOB, "mysql"), nullable=False),
    )
    op.create_table(
        "model_source_manifest",
        sa.Column("digest", sa.String(64), primary_key=True),
        sa.Column("manifest", sa.JSON(), nullable=False),
    )
    op.create_table(
        "model_source_version",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("definition_id", sa.Integer(), sa.ForeignKey("bpmn_process_definition.id"), nullable=False),
        sa.Column("manifest_digest", sa.String(64), sa.ForeignKey("model_source_manifest.digest"), nullable=False),
        sa.UniqueConstraint("definition_id", "manifest_digest", name="model_source_version_unique"),
    )
    op.create_index("ix_model_source_version_definition_id", "model_source_version", ["definition_id"])
    op.create_index("ix_model_source_version_manifest_digest", "model_source_version", ["manifest_digest"])
    with op.batch_alter_table("process_instance") as batch:
        batch.add_column(sa.Column("source_manifest_id", sa.String(64), nullable=True))
        batch.create_foreign_key(
            "fk_process_instance_source_manifest", "model_source_manifest", ["source_manifest_id"], ["digest"]
        )
        batch.create_index("ix_process_instance_source_manifest_id", ["source_manifest_id"])

    with op.batch_alter_table("process_instance_migration_detail") as batch:
        batch.add_column(sa.Column("initial_source_manifest_id", sa.String(64), nullable=True))
        batch.add_column(sa.Column("target_source_manifest_id", sa.String(64), nullable=True))


def downgrade():
    with op.batch_alter_table("process_instance_migration_detail") as batch:
        batch.drop_column("initial_source_manifest_id")
        batch.drop_column("target_source_manifest_id")
    with op.batch_alter_table("process_instance") as batch:
        batch.drop_index("ix_process_instance_source_manifest_id")
        batch.drop_constraint("fk_process_instance_source_manifest", type_="foreignkey")
        batch.drop_column("source_manifest_id")
    op.drop_table("model_source_version")
    op.drop_table("model_source_manifest")
    op.drop_table("model_source_blob")

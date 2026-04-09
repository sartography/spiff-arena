from pathlib import Path

from spiffworkflow_backend.services.migration_guard import get_file_heads
from spiffworkflow_backend.services.migration_guard import needs_upgrade


def test_get_file_heads_uses_down_revision_metadata() -> None:
    versions_dir = (
        Path(__file__).resolve().parents[3] / "migrations" / "versions"
    )

    file_heads = get_file_heads(versions_dir)

    assert "a1b2c3d4e5f6" in file_heads
    assert "0b90171055cd" not in file_heads


def test_needs_upgrade_when_db_revision_is_not_a_file_head() -> None:
    file_heads = ["a1b2c3d4e5f6"]

    assert needs_upgrade(["0b90171055cd"], file_heads) is True
    assert needs_upgrade(["a1b2c3d4e5f6"], file_heads) is False

from __future__ import annotations

import ast
from collections.abc import Iterable
from pathlib import Path


def _literal_string_list(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Constant):
        if node.value is None:
            return []
        if isinstance(node.value, str):
            return [node.value]
    if isinstance(node, ast.List | ast.Tuple | ast.Set):
        values: list[str] = []
        for element in node.elts:
            if isinstance(element, ast.Constant) and isinstance(element.value, str):
                values.append(element.value)
        return values
    return []


def _parse_migration_file(path: Path) -> tuple[str | None, list[str]]:
    tree = ast.parse(path.read_text())

    revision: str | None = None
    down_revisions: list[str] = []

    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if not isinstance(target, ast.Name):
                continue
            if target.id == "revision":
                revision_values = _literal_string_list(node.value)
                revision = revision_values[0] if revision_values else None
            elif target.id == "down_revision":
                down_revisions = _literal_string_list(node.value)

    return revision, down_revisions


def get_file_heads(versions_dir: Path) -> list[str]:
    all_revision_ids: set[str] = set()
    all_down_revisions: set[str] = set()

    for path in sorted(versions_dir.glob("*.py")):
        revision, down_revisions = _parse_migration_file(path)
        if revision is None:
            continue
        all_revision_ids.add(revision)
        all_down_revisions.update(down_revisions)

    return sorted(all_revision_ids - all_down_revisions)


def needs_upgrade(
    db_current_revisions: Iterable[str],
    file_heads: Iterable[str],
) -> bool:
    current_revisions = [revision for revision in db_current_revisions if revision]
    if not current_revisions:
        return True

    heads_set = set(file_heads)
    return any(revision not in heads_set for revision in current_revisions)

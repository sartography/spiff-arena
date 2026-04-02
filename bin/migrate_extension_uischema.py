#!/usr/bin/env -S uv run --script
"""Migrate extension_uischema.json files from 0.1/0.2 to 1.0."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def normalize_json(data: Any) -> str:
    return json.dumps(data, indent=2) + "\n"


def migrate_ux_element(ux_element: dict[str, Any]) -> tuple[str, dict[str, Any]] | dict[str, Any]:
    display_location = ux_element["display_location"]

    if display_location == "css":
        css_file = ux_element["location_specific_configs"]["css_file"]
        return ("stylesheet", {"file": css_file})

    if display_location == "routes":
        return ("route", {"path": ux_element["page"]})

    location_map = {
        "header_menu_item": "primary_nav",
        "primary_nav_item": "primary_nav",
        "user_profile_item": "user_menu",
        "configuration_tab_item": "configuration_tab",
    }
    target_type = "path" if ux_element.get("use_full_page_path") else "extension_page"
    navigation_item: dict[str, Any] = {
        "label": ux_element["label"],
        "location": location_map[display_location],
        "target": {
            "type": target_type,
            "path": ux_element["page"],
        },
    }
    if ux_element.get("icon"):
        navigation_item["icon"] = ux_element["icon"]
    if ux_element.get("tooltip"):
        navigation_item["tooltip"] = ux_element["tooltip"]
    location_specific_configs = ux_element.get("location_specific_configs") or {}
    if location_specific_configs.get("highlight_on_tabs"):
        navigation_item["highlight_on_tabs"] = location_specific_configs["highlight_on_tabs"]
    return navigation_item


def migrate_schema(data: dict[str, Any]) -> dict[str, Any]:
    version = data.get("version")
    if version == "1.0":
        return data
    if version not in {"0.1", "0.2"}:
        raise ValueError(f"Unsupported extension ui schema version: {version!r}")

    migrated: dict[str, Any] = {"version": "1.0"}
    if data.get("disabled") is True:
        migrated["disabled"] = True

    navigation: list[dict[str, Any]] = []
    routes: list[dict[str, str]] = []
    stylesheets: list[dict[str, str]] = []

    for ux_element in data.get("ux_elements", []):
        migrated_item = migrate_ux_element(ux_element)
        if isinstance(migrated_item, tuple):
            kind, payload = migrated_item
            if kind == "route":
                routes.append(payload)
            elif kind == "stylesheet":
                stylesheets.append(payload)
            else:
                raise ValueError(f"Unsupported migrated ux element kind: {kind}")
        else:
            navigation.append(migrated_item)

    if navigation:
        migrated["navigation"] = navigation
    if routes:
        migrated["routes"] = routes
    if stylesheets:
        migrated["assets"] = {"stylesheets": stylesheets}
    if data.get("pages"):
        migrated["pages"] = data["pages"]

    return migrated


def iter_extension_files(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    return sorted(path.rglob("extension_uischema.json"))


def process_file(file_path: Path, write: bool) -> bool:
    original = json.loads(file_path.read_text())
    migrated = migrate_schema(original)
    original_text = normalize_json(original)
    migrated_text = normalize_json(migrated)
    changed = original_text != migrated_text
    if write and changed:
        file_path.write_text(migrated_text)
    return changed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="extension_uischema.json file or directory to migrate")
    parser.add_argument("--write", action="store_true", help="overwrite files in place")
    parser.add_argument("--stdout", action="store_true", help="print migrated output for a single file")
    parser.add_argument("--check", action="store_true", help="exit non-zero if any file would change")
    args = parser.parse_args()

    file_paths: list[Path] = []
    for raw_path in args.paths:
        file_paths.extend(iter_extension_files(Path(raw_path).expanduser()))

    if args.stdout:
        if len(file_paths) != 1:
            raise SystemExit("--stdout requires exactly one extension_uischema.json input")
        migrated = migrate_schema(json.loads(file_paths[0].read_text()))
        print(normalize_json(migrated), end="")
        return 0

    changed_files: list[Path] = []
    for file_path in file_paths:
        if process_file(file_path, write=args.write):
            changed_files.append(file_path)

    if args.check and changed_files:
        for file_path in changed_files:
            print(file_path)
        return 1

    if not args.write:
        for file_path in changed_files:
            print(file_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

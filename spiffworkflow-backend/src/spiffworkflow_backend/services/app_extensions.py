"""Load explicitly named, trusted app extensions from the model repository."""

import json
import re
import sys
from importlib.util import module_from_spec
from importlib.util import spec_from_file_location
from pathlib import Path
from uuid import uuid4

from flask import Flask


def init_app_extensions(app: Flask) -> None:
    names = app.config.get("SPIFFWORKFLOW_BACKEND_APP_EXTENSIONS", [])
    if isinstance(names, str):
        names = json.loads(names)
    if not isinstance(names, list) or not all(
        isinstance(name, str) and re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name) for name in names
    ):
        raise ValueError("SPIFFWORKFLOW_BACKEND_APP_EXTENSIONS must be a JSON list of extension package names")
    if len(names) != len(set(names)):
        raise ValueError("Duplicate application extension names")
    if not names:
        return
    root = Path(app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]).resolve()
    for name in names:
        package = (root / "extensions" / name).resolve()
        source = (package / "__init__.py").resolve()
        if not package.is_relative_to(root / "extensions") or not source.is_relative_to(package):
            raise ValueError(f"Application extension escapes its repository package: {name!r}")
        if not source.is_file():
            raise FileNotFoundError(f"Application extension initializer not found: {source}")
        # Private package identity supports relative imports without sys.path edits
        # or cross-app collisions when two repositories use the same extension name.
        module_name = f"_arena_app_extension_{uuid4().hex}"
        spec = spec_from_file_location(module_name, source, submodule_search_locations=[str(package)])
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load application extension: {name}")
        module = module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            module.init_app(app)
        except BaseException:
            for key in list(sys.modules):
                if key == module_name or key.startswith(f"{module_name}."):
                    del sys.modules[key]
            raise

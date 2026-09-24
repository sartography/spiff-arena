import sys
from pathlib import Path

import pytest
from flask import Flask

from spiffworkflow_backend.services.app_extensions import init_app_extensions


def make_extension(root: Path, name: str, source: str) -> Path:
    package = root / "extensions" / name
    package.mkdir(parents=True)
    (package / "__init__.py").write_text(source)
    return package


def configured_app(root: Path, names: object) -> Flask:
    app = Flask(__name__)
    app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"] = str(root)
    app.config["SPIFFWORKFLOW_BACKEND_APP_EXTENSIONS"] = names
    return app


def test_disabled_needs_no_repository() -> None:
    init_app_extensions(Flask(__name__))


@pytest.mark.parametrize("names", ['["first", "second"]', ["first", "second"]])
def test_relative_imports_and_initialization_order(tmp_path: Path, names: object) -> None:
    package = make_extension(
        tmp_path,
        "first",
        "from .helper import VALUE\ndef init_app(app):\n    app.extensions['calls'] = [VALUE]\n",
    )
    (package / "helper.py").write_text("VALUE = 'first'\n")
    make_extension(tmp_path, "second", "def init_app(app):\n    app.extensions['calls'].append('second')\n")
    app = configured_app(tmp_path, names)
    original_path = list(sys.path)
    init_app_extensions(app)
    assert app.extensions["calls"] == ["first", "second"]
    assert sys.path == original_path
    assert "first" not in sys.modules


@pytest.mark.parametrize(
    "names", ["{}", "null", "[1]", ["../escape"], ["/absolute"], ["pkg:init_app"], ["pkg.name"], [""], ["same", "same"]]
)
def test_invalid_configuration_fails(tmp_path: Path, names: object) -> None:
    with pytest.raises(ValueError):
        init_app_extensions(configured_app(tmp_path, names))


def test_missing_package_fails(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        init_app_extensions(configured_app(tmp_path, ["missing"]))


@pytest.mark.parametrize("escape", ["directory", "initializer"])
def test_symlink_escape_fails(tmp_path: Path, escape: str) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "__init__.py").write_text("raise AssertionError('must not run')\n")
    root = tmp_path / "models"
    (root / "extensions").mkdir(parents=True)
    package = root / "extensions" / "escape"
    if escape == "directory":
        package.symlink_to(outside, target_is_directory=True)
    else:
        package.mkdir()
        (package / "__init__.py").symlink_to(outside / "__init__.py")
    with pytest.raises(ValueError, match="escapes"):
        init_app_extensions(configured_app(root, ["escape"]))


def test_repositories_with_same_name_are_isolated(tmp_path: Path) -> None:
    for value in ("one", "two"):
        root = tmp_path / value
        package = make_extension(
            root, "example", "from .helper import VALUE\ndef init_app(app):\n    app.extensions['value'] = VALUE\n"
        )
        (package / "helper.py").write_text(f"VALUE = {value!r}\n")
        app = configured_app(root, ["example"])
        init_app_extensions(app)
        assert app.extensions["value"] == value


def test_initializer_failure_propagates_and_cleans_modules(tmp_path: Path) -> None:
    package = make_extension(
        tmp_path, "broken", "from . import helper\ndef init_app(app):\n    raise RuntimeError('missing schema')\n"
    )
    (package / "helper.py").write_text("VALUE = 1\n")
    before = {name for name in sys.modules if name.startswith("_arena_app_extension_")}
    with pytest.raises(RuntimeError, match="missing schema"):
        init_app_extensions(configured_app(tmp_path, ["broken"]))
    assert {name for name in sys.modules if name.startswith("_arena_app_extension_")} == before

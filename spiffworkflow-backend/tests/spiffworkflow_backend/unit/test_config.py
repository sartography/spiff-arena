import importlib
import os

import pytest
from flask import Flask

from spiffworkflow_backend.config import detect_database_type_from_uri
from spiffworkflow_backend.config import setup_database_configs
from spiffworkflow_backend.config.normalized_environment import normalized_environment


def test_uppercase_auth_config_environment_keys_are_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    """Windows-style uppercase auth variables load with lowercase nested keys."""
    from spiffworkflow_backend.config import default

    try:
        with monkeypatch.context() as patched:
            for key in list(os.environ):
                if key.upper().startswith("SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__"):
                    patched.delenv(key)
            patched.setenv("SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__0__IDENTIFIER", "windows-test")
            patched.setenv("SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__0__URI", "http://localhost:7000/openid")
            patched.setenv("SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__0__CLIENT_ID", "spiffworkflow-backend")
            importlib.reload(default)

            assert default.SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS == [
                {
                    "identifier": "windows-test",
                    "uri": "http://localhost:7000/openid",
                    "client_id": "spiffworkflow-backend",
                }
            ]
    finally:
        importlib.reload(default)


def test_auth_config_keys_differing_only_by_case_are_rejected() -> None:
    """Case variants of the same auth key must not silently overwrite each other."""
    from spiffworkflow_backend.config import default

    with pytest.raises(ValueError, match="Duplicate authentication config key: URI"):
        default.lowercase_config_keys([{"uri": "https://first.example/openid", "URI": "https://second.example/openid"}])


def test_case_variant_auth_environment_paths_are_rejected() -> None:
    """The structured environment parser must preserve case variants for validation."""
    from spiffworkflow_backend.config import default

    structured = normalized_environment(
        {
            "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__0__uri": "https://first.example/openid",
            "SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS__0__URI": "https://second.example/openid",
        }
    )

    with pytest.raises(ValueError, match="Duplicate authentication config key: URI"):
        default.lowercase_config_keys(structured["SPIFFWORKFLOW_BACKEND_AUTH_CONFIGS"])


def test_mysql_database_type_is_inferred_from_uri() -> None:
    database_uri = "mysql+mysqldb://root:pwd@127.0.0.1/spiffworkflow_backend_unit_testing"
    database_type = detect_database_type_from_uri(database_uri)
    assert database_type == "mysql"


def test_postgres_database_type_is_inferred_from_uri() -> None:
    database_uri = "postgresql://spiffworkflow_backend:spiffworkflow_backend@localhost:5432/spiffworkflow_backend_unit_testing"
    database_type = detect_database_type_from_uri(database_uri)
    assert database_type == "postgres"


def test_sqlite_database_type_is_inferred_from_uri() -> None:
    database_uri = "sqlite:///db_unit_testing.sqlite3"
    database_type = detect_database_type_from_uri(database_uri)
    assert database_type == "sqlite"


def test_empty_database_uri_returns_none() -> None:
    assert detect_database_type_from_uri("") is None
    assert detect_database_type_from_uri(None) is None


def test_postgresql_scheme_is_normalized_to_postgres() -> None:
    database_uri = "postgresql+psycopg2://user:pass@localhost/db"
    database_type = detect_database_type_from_uri(database_uri)
    assert database_type == "postgres"


@pytest.mark.parametrize(
    ("hide_parameters_config", "expected"),
    [(None, False), (False, False), (True, True)],
)
def test_setup_database_configs_sets_hide_parameters(hide_parameters_config: bool | None, expected: bool) -> None:
    app = Flask(__name__)
    app.config.update(
        ENV_IDENTIFIER="unit_testing",
        SPIFFWORKFLOW_BACKEND_DATABASE_URI="sqlite:///db_unit_testing.sqlite3",
        SPIFFWORKFLOW_BACKEND_DATABASE_POOL_SIZE="5",
        SPIFFWORKFLOW_BACKEND_DATABASE_POOL_PRE_PING=True,
        SPIFFWORKFLOW_BACKEND_DATABASE_HIDE_PARAMETERS=hide_parameters_config,
    )

    setup_database_configs(app)

    assert app.config["SQLALCHEMY_ENGINE_OPTIONS"]["hide_parameters"] is expected

import importlib

import pytest

from spiffworkflow_backend.config import detect_database_type_from_uri


def test_uppercase_auth_config_environment_keys_are_normalized(monkeypatch: pytest.MonkeyPatch) -> None:
    from spiffworkflow_backend.config import default

    try:
        with monkeypatch.context() as patched:
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

import pytest
from flask import Flask

from spiffworkflow_backend.config import detect_database_type_from_uri
from spiffworkflow_backend.config import setup_database_configs


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

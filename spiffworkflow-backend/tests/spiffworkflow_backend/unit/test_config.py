import unittest

from spiffworkflow_backend.config import detect_database_type_from_uri


class TestConfig(unittest.TestCase):
    def test_mysql_database_type_is_inferred_from_uri(self) -> None:
        database_uri = "mysql+mysqldb://root:pwd@127.0.0.1/spiffworkflow_backend_unit_testing"
        database_type = detect_database_type_from_uri(database_uri)
        self.assertEqual(database_type, "mysql")

    def test_postgres_database_type_is_inferred_from_uri(self) -> None:
        database_uri = (
            "postgresql://spiffworkflow_backend:spiffworkflow_backend@localhost:5432/spiffworkflow_backend_unit_testing"
        )
        database_type = detect_database_type_from_uri(database_uri)
        self.assertEqual(database_type, "postgres")

    def test_sqlite_database_type_is_inferred_from_uri(self) -> None:
        database_uri = "sqlite:///db_unit_testing.sqlite3"
        database_type = detect_database_type_from_uri(database_uri)
        self.assertEqual(database_type, "sqlite")

    def test_empty_database_uri_returns_none(self) -> None:
        self.assertIsNone(detect_database_type_from_uri(""))
        self.assertIsNone(detect_database_type_from_uri(None))

    def test_postgresql_scheme_is_normalized_to_postgres(self) -> None:
        database_uri = "postgresql+psycopg2://user:pass@localhost/db"
        database_type = detect_database_type_from_uri(database_uri)
        self.assertEqual(database_type, "postgres")

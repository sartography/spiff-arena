import importlib
import os
import unittest
from unittest.mock import patch

import spiffworkflow_backend.config.default as default_config
from spiffworkflow_backend import create_app


class TestConfig(unittest.TestCase):
    def test_mysql_database_type_is_inferred_from_uri(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SPIFFWORKFLOW_BACKEND_DATABASE_TYPE": "",
                "SPIFFWORKFLOW_BACKEND_DATABASE_URI": "mysql+mysqldb://root:pwd@127.0.0.1/spiffworkflow_backend_unit_testing",
            },
        ):
            importlib.reload(default_config)
            app = create_app()
            self.assertEqual(app.app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"], "mysql")

    def test_postgres_database_type_is_inferred_from_uri(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SPIFFWORKFLOW_BACKEND_DATABASE_TYPE": "",
                "SPIFFWORKFLOW_BACKEND_DATABASE_URI": "postgresql://spiffworkflow_backend:spiffworkflow_backend@localhost:5432/spiffworkflow_backend_unit_testing",
            },
        ):
            importlib.reload(default_config)
            app = create_app()
            self.assertEqual(app.app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"], "postgres")

    def test_sqlite_database_type_is_inferred_from_uri(self) -> None:
        with patch.dict(
            os.environ,
            {
                "SPIFFWORKFLOW_BACKEND_DATABASE_TYPE": "",
                "SPIFFWORKFLOW_BACKEND_DATABASE_URI": "sqlite:///db_unit_testing.sqlite3",
            },
        ):
            importlib.reload(default_config)
            app = create_app()
            self.assertEqual(app.app.config["SPIFFWORKFLOW_BACKEND_DATABASE_TYPE"], "sqlite")

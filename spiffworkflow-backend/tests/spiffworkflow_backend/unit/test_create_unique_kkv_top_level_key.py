from collections.abc import Generator
from dataclasses import dataclass
from typing import Any

import pytest
from flask.app import Flask
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.scripts.create_unique_kkv_top_level_key import CreateUniqueKKVTopLevelKey

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def with_clean_data_store(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[None, None, None]:
    db.session.query(KKVDataStoreModel).delete()
    db.session.commit()
    yield


class TestCreateUniqueKKVTopLevelKey(BaseTest):
    """Infer from class name."""

    def test_creates_unique_top_level_keys(self, with_clean_data_store: None) -> None:
        prefix = "study_"
        ids = [
            CreateUniqueKKVTopLevelKey().run(None, prefix),
            CreateUniqueKKVTopLevelKey().run(None, prefix),
            CreateUniqueKKVTopLevelKey().run(None, prefix),
            CreateUniqueKKVTopLevelKey().run(None, prefix),
            CreateUniqueKKVTopLevelKey().run(None, prefix),
            CreateUniqueKKVTopLevelKey().run(None, prefix),
            CreateUniqueKKVTopLevelKey().run(None, prefix),
        ]
        unique_ids = set(ids)
        assert len(ids) == len(unique_ids)

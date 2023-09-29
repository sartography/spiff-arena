from collections.abc import Generator

import pytest
from flask.app import Flask
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def with_loaded_reference_cache(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[None, None, None]:
    yield


class TestReferenceCacheService(BaseTest):
    def test_upsearch_locations(
        self,
    ) -> None:
        locations = ReferenceCacheService.upsearch_locations("misc/jonjon/generic-data-store-area/test-level-2")
        assert locations == [
            "misc/jonjon/generic-data-store-area/test-level-2",
            "misc/jonjon/generic-data-store-area",
            "misc/jonjon",
            "misc",
        ]

    def test_can_find_location(self, with_loaded_reference_cache: None) -> None:
        # TODO: set up generation and cache entries
        location = ReferenceCacheService.upsearch(
            "misc/jonjon/generic-data-store-area/test-level-1", "contacts_datastore", "data_store"
        )
        assert location == "misc/jonjon/generic-data-store-area/test-level-1"

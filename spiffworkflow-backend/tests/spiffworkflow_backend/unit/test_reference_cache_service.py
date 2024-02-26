from collections.abc import Generator

import pytest
from flask.app import Flask
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


@pytest.fixture()
def with_loaded_reference_cache(app: Flask, with_db_and_bpmn_file_cleanup: None) -> Generator[None, None, None]:
    reference_objects: dict[str, ReferenceCacheModel] = {}
    ReferenceCacheService.add_unique_reference_cache_object(
        reference_objects,
        ReferenceCacheModel.from_params(
            "contacts_datastore_root",
            "Contacts Datastore Root",
            "data_store",
            "contacts_datastore.bpmn",
            "",
            None,
            False,
        ),
    )
    ReferenceCacheService.add_unique_reference_cache_object(
        reference_objects,
        ReferenceCacheModel.from_params(
            "contacts_datastore",
            "contacts_datastore",
            "data_store",
            "contacts_datastore.bpmn",
            "misc/jonjon",
            None,
            False,
        ),
    )
    ReferenceCacheService.add_unique_reference_cache_object(
        reference_objects,
        ReferenceCacheModel.from_params(
            "contacts_datastore",
            "contacts_datastore",
            "data_store",
            "contacts_datastore.bpmn",
            "misc/jonjon/generic-data-store-area/test-level-1",
            None,
            False,
        ),
    )

    ReferenceCacheService.add_new_generation(reference_objects)
    yield


class TestReferenceCacheService(BaseTest):
    def test_can_find_data_store_in_current_location(self, with_loaded_reference_cache: None) -> None:
        location = ReferenceCacheService.upsearch(
            "misc/jonjon/generic-data-store-area/test-level-1", "contacts_datastore", "data_store"
        )
        assert location == "misc/jonjon/generic-data-store-area/test-level-1"

    def test_can_find_data_store_in_upsearched_location(self, with_loaded_reference_cache: None) -> None:
        location = ReferenceCacheService.upsearch(
            "misc/jonjon/generic-data-store-area/test-level-2", "contacts_datastore", "data_store"
        )
        assert location == "misc/jonjon"

    def test_does_not_find_data_store_in_non_upsearched_location(self, with_loaded_reference_cache: None) -> None:
        location = ReferenceCacheService.upsearch("some/other/place", "contacts_datastore", "data_store")
        assert location is None

    def test_can_find_data_store_in_upsearched_root_location(self, with_loaded_reference_cache: None) -> None:
        location = ReferenceCacheService.upsearch(
            "misc/jonjon/generic-data-store-area/test-level-2", "contacts_datastore_root", "data_store"
        )
        assert location == ""

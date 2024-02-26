from spiffworkflow_backend.services.upsearch_service import UpsearchService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUpsearchService(BaseTest):
    def test_upsearch_locations(
        self,
    ) -> None:
        locations = UpsearchService.upsearch_locations("misc/jonjon/generic-data-store-area/test-level-2")
        assert locations == [
            "misc/jonjon/generic-data-store-area/test-level-2",
            "misc/jonjon/generic-data-store-area",
            "misc/jonjon",
            "misc",
            "",
        ]

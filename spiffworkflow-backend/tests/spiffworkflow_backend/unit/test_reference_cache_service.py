import json
import os
import tempfile
from collections.abc import Generator

from flask.app import Flask
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest

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

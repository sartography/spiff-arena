from typing import Any

from flask import jsonify
from flask import make_response

from spiffworkflow_backend.services.upsearch_service import UpsearchService


def upsearch_locations(
    location: str | None,
) -> Any:
    upsearch_locations = UpsearchService.upsearch_locations(location)

    return make_response(jsonify({"locations": upsearch_locations}), 200)

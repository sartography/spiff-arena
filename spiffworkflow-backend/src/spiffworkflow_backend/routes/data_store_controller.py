"""APIs for dealing with process groups, process models, and process instances."""

from typing import Any

import flask.wrappers
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.data_stores.json import JSONDataStore
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.data_stores.typeahead import TypeaheadDataStore
from spiffworkflow_backend.exceptions.api_error import ApiError


def data_store_list() -> flask.wrappers.Response:
    """Returns a list of the names of all the data stores."""
    data_stores = []

    # Right now the only data stores we support are type ahead, kkv, json

    data_stores.extend(JSONDataStore.existing_data_stores())
    data_stores.extend(TypeaheadDataStore.existing_data_stores())
    data_stores.extend(KKVDataStore.existing_data_stores())

    return make_response(jsonify(data_stores), 200)


def _build_response(data_store_class: Any, name: str, page: int, per_page: int) -> flask.wrappers.Response:
    data_store_query = data_store_class.query_data_store(name)
    data = data_store_query.paginate(page=page, per_page=per_page, error_out=False)
    results = []
    for item in data.items:
        result = data_store_class.build_response_item(item)
        results.append(result)
    response_json = {
        "results": results,
        "pagination": {
            "count": len(data.items),
            "total": data.total,
            "pages": data.pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def data_store_item_list(
    data_store_type: str, name: str, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Returns a list of the items in a data store."""

    if data_store_type == "typeahead":
        return _build_response(TypeaheadDataStore, name, page, per_page)

    if data_store_type == "kkv":
        return _build_response(KKVDataStore, name, page, per_page)

    if data_store_type == "json":
        return _build_response(JSONDataStore, name, page, per_page)

    raise ApiError("unknown_data_store", f"Unknown data store type: {data_store_type}", status_code=400)

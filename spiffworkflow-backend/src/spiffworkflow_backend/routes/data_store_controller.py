"""APIs for dealing with process groups, process models, and process instances."""
import json
from typing import Any

import flask.wrappers
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.data_stores.json import JSONDataStore
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.data_stores.typeahead import TypeaheadDataStore
from spiffworkflow_backend.exceptions.api_error import ApiError

DATA_STORES = {
    "json": (JSONDataStore, "JSON Data Store"),
    "kkv": (KKVDataStore, "Keyed Key-Value Data Store"),
    "typehead": (TypeaheadDataStore, "Typeahead Data Store"),
}


def data_store_list() -> flask.wrappers.Response:
    """Returns a list of the names of all the data stores."""
    data_stores = []

    # Right now the only data stores we support are type ahead, kkv, json

    data_stores.extend(JSONDataStore.existing_data_stores())
    data_stores.extend(TypeaheadDataStore.existing_data_stores())
    data_stores.extend(KKVDataStore.existing_data_stores())

    return make_response(jsonify(data_stores), 200)


def data_store_types() -> flask.wrappers.Response:
    """Returns a list of the types of available data stores."""

    # this if == "json" check is temporary while we roll out support for other data stores
    # being created with locations, identifiers and schemas
    data_store_types = [{"type": k, "name": v[0].__name__, "description": v[1]} for k, v in DATA_STORES.items() if k == "json"]

    return make_response(jsonify(data_store_types), 200)


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


def data_store_item_list(data_store_type: str, name: str, page: int = 1, per_page: int = 100) -> flask.wrappers.Response:
    """Returns a list of the items in a data store."""

    if data_store_type not in DATA_STORES:
        raise ApiError("unknown_data_store", f"Unknown data store type: {data_store_type}", status_code=400)

    data_store_class, _ = DATA_STORES[data_store_type]
    return _build_response(data_store_class, name, page, per_page)


def data_store_create(body: dict) -> flask.wrappers.Response:
    try:
        data_store_type = body["type"]
        name = body["name"]
        identifier = body["id"]
        location = body["location"]
        description = body.get("description")
        schema = body["schema"]
    except Exception as e:
        raise ApiError(
            "data_store_required_key_missing",
            "A valid JSON Schema is required when creating a new data store instance.",
            status_code=400,
        ) from e

    try:
        schema = json.loads(schema)
    except Exception as e:
        raise ApiError(
            "data_store_invalid_schema",
            "A valid JSON Schema is required when creating a new data store instance.",
            status_code=400,
        ) from e

    if data_store_type not in DATA_STORES:
        raise ApiError("unknown_data_store", f"Unknown data store type: {data_store_type}", status_code=400)

    data_store_class, _ = DATA_STORES[data_store_type]
    data_store_class.create_instance(name, identifier, location, schema, description)

    return make_response(jsonify({"ok": True}), 200)

import json
from typing import Any

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.data_stores.json import JSONDataStore
from spiffworkflow_backend.data_stores.kkv import KKVDataStore
from spiffworkflow_backend.data_stores.typeahead import TypeaheadDataStore
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.upsearch_service import UpsearchService

DATA_STORES = {
    "json": (JSONDataStore, "JSON Data Store"),
    "kkv": (KKVDataStore, "Keyed Key-Value Data Store"),
    "typeahead": (TypeaheadDataStore, "Typeahead Data Store"),
}


def data_store_list(
    process_group_identifier: str | None = None, upsearch: bool = False, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Returns a list of the names of all the data stores."""
    data_stores = []
    locations_to_upsearch = []

    if process_group_identifier is not None:
        if upsearch:
            locations_to_upsearch = UpsearchService.upsearch_locations(process_group_identifier)
        else:
            locations_to_upsearch.append(process_group_identifier)

    # Right now the only data stores we support are type ahead, kkv, json

    data_stores.extend(JSONDataStore.existing_data_stores(locations_to_upsearch))
    data_stores.extend(TypeaheadDataStore.existing_data_stores(locations_to_upsearch))
    data_stores.extend(KKVDataStore.existing_data_stores(locations_to_upsearch))

    return make_response(jsonify(data_stores), 200)


def data_store_types() -> flask.wrappers.Response:
    """Returns a list of the types of available data stores."""

    # this if != "typeahead" check is temporary while we roll out support for other data stores
    # being created with locations, identifiers and schemas
    data_store_types = [
        {"type": k, "name": v[0].__name__, "description": v[1]} for k, v in DATA_STORES.items() if k != "typeahead"
    ]

    return make_response(jsonify(data_store_types), 200)


def _build_response(
    data_store_class: Any, identifier: str, location: str | None, page: int, per_page: int
) -> flask.wrappers.Response:
    data_store_query = data_store_class.get_data_store_query(identifier, location)
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
    data_store_type: str, identifier: str, location: str | None = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Returns a list of the items in a data store."""

    if data_store_type not in DATA_STORES:
        raise ApiError("unknown_data_store", f"Unknown data store type: {data_store_type}", status_code=400)

    data_store_class, _ = DATA_STORES[data_store_type]
    return _build_response(data_store_class, identifier, location, page, per_page)


def data_store_create(body: dict) -> flask.wrappers.Response:
    return _data_store_upsert(body, True)


def data_store_update(body: dict) -> flask.wrappers.Response:
    return _data_store_upsert(body, False)


def _data_store_upsert(body: dict, insert: bool) -> flask.wrappers.Response:
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

    if insert:
        data_store_model = data_store_class.create_instance(identifier, location)
    else:
        data_store_model = data_store_class.existing_instance(identifier, location)

    data_store_model.name = name
    data_store_model.schema = schema
    data_store_model.description = description or ""

    _write_specification_to_process_group(data_store_type, data_store_model)

    db.session.add(data_store_model)
    db.session.commit()

    _commit_and_push_to_git(f"User: {g.user.username} added data store {data_store_model.identifier}")
    return make_response(jsonify({"ok": True}), 200)


def _write_specification_to_process_group(
    data_store_type: str, data_store_model: JSONDataStore | KKVDataStore | TypeaheadDataStore
) -> None:
    process_group = ProcessModelService.get_process_group(
        data_store_model.location, find_direct_nested_items=False, find_all_nested_items=False, create_if_not_exists=True
    )

    if data_store_type not in process_group.data_store_specifications:
        process_group.data_store_specifications[data_store_type] = {}

    process_group.data_store_specifications[data_store_type][data_store_model.identifier] = {
        "name": data_store_model.name,
        "identifier": data_store_model.identifier,
        "location": data_store_model.location,
        "schema": data_store_model.schema,
        "description": data_store_model.description,
    }

    ProcessModelService.update_process_group(process_group)


def data_store_show(data_store_type: str, identifier: str, process_group_identifier: str) -> flask.wrappers.Response:
    """Returns a description of a data store."""

    if data_store_type not in DATA_STORES:
        raise ApiError("unknown_data_store", f"Unknown data store type: {data_store_type}", status_code=400)

    data_store_class, _ = DATA_STORES[data_store_type]
    data_store_query = data_store_class.get_data_store_query(identifier, process_group_identifier)
    result = data_store_query.first()

    if result is None:
        raise ApiError(
            "could_not_locate_data_store",
            f"Could not locate data store type: {data_store_type} for process group: {process_group_identifier}",
            status_code=400,
        )

    response = {
        "name": result.name,
        "location": result.location,
        "type": data_store_type,
        "id": result.identifier,
        "schema": result.schema,
        "description": result.description,
    }

    return make_response(jsonify(response), 200)

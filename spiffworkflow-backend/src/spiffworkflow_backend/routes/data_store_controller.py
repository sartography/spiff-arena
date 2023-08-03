"""APIs for dealing with process groups, process models, and process instances."""

import flask.wrappers
from flask import jsonify
from flask import make_response

from spiffworkflow_backend import db
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.typeahead import TypeaheadModel


def data_store_list() -> flask.wrappers.Response:
    """Returns a list of the names of all the data stores."""
    data_stores = []

    # Right now the only data store we support is type ahead

    for cat in db.session.query(TypeaheadModel.category).distinct().order_by(TypeaheadModel.category):  # type: ignore
        data_stores.append({"name": cat[0], "type": "typeahead"})

    return make_response(jsonify(data_stores), 200)


def data_store_item_list(
    data_store_type: str, name: str, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    """Returns a list of the items in a data store."""
    if data_store_type == "typeahead":
        data_store_query = TypeaheadModel.query.filter_by(category=name).order_by(
            TypeaheadModel.category, TypeaheadModel.search_term
        )
        data = data_store_query.paginate(page=page, per_page=per_page, error_out=False)
        results = []
        for typeahead in data.items:
            result = typeahead.result
            result["search_term"] = typeahead.search_term
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
    else:
        raise ApiError("unknown_data_store", f"Unknown data store type: {data_store_type}", status_code=400)

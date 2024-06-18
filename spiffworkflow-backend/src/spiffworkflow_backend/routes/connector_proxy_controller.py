import json
from typing import Any

import flask.wrappers
from flask import current_app
from flask.wrappers import Response
from security import safe_requests  # type: ignore

from spiffworkflow_backend.config import HTTP_REQUEST_TIMEOUT_SECONDS
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.typeahead import TypeaheadModel


def connector_proxy_typeahead_url() -> Any:
    """Returns the connector proxy type ahead url."""
    return current_app.config["SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_TYPEAHEAD_URL"]


def typeahead(category: str, prefix: str, limit: int) -> flask.wrappers.Response:
    if _has_local_data(category):
        return _local_typeahead(category, prefix, limit)

    return _remote_typeahead(category, prefix, limit)


def _local_typeahead(category: str, prefix: str, limit: int) -> flask.wrappers.Response:
    results = (
        db.session.query(TypeaheadModel.result)
        .filter(
            TypeaheadModel.category == category,
            TypeaheadModel.search_term.ilike(f"{prefix}%"),  # type: ignore
        )
        .order_by(TypeaheadModel.search_term)
        .limit(limit)
        .all()
        or []
    )

    # this is a bummer but sqlalchemy returns a tuple of one field for each result
    results = [result[0] for result in results]

    response = json.dumps(results)

    return Response(response, status=200, mimetype="application/json")


def _remote_typeahead(category: str, prefix: str, limit: int) -> flask.wrappers.Response:
    url = f"{connector_proxy_typeahead_url()}/v1/typeahead/{category}?prefix={prefix}&limit={limit}"

    proxy_response = safe_requests.get(url, timeout=HTTP_REQUEST_TIMEOUT_SECONDS)
    status = proxy_response.status_code
    response = proxy_response.text

    return Response(response, status=status, mimetype="application/json")


def _has_local_data(category: str) -> bool:
    return db.session.query(TypeaheadModel.category).filter_by(category=category).first() is not None

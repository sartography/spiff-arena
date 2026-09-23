"""Optional process model history supplied by a deployment app extension."""

from typing import Any

from flask import current_app
from flask import has_app_context

from spiffworkflow_backend.models.db import db


def process_model_history(instance_id: int | None = None) -> Any:
    if not has_app_context():  # type: ignore[no-untyped-call]
        return None
    factory = current_app.extensions.get("process_model_history")
    return factory(db.session, instance_id) if factory else None

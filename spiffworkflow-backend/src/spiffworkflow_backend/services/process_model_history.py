"""Optional process model history supplied by a deployment app extension."""

from typing import Any

from flask import current_app
from flask import has_app_context

from spiffworkflow_backend.models.db import db


def process_model_history(instance_id: int | None = None) -> Any:
    if not has_app_context():  # type: ignore[no-untyped-call]
        return None
    factory = current_app.extensions.get("process_model_history")
    history = factory(db.session) if factory else None
    if history is not None and instance_id is not None and not history.has_snapshot(instance_id):
        return None
    return history

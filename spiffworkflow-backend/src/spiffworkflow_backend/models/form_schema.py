from __future__ import annotations

import json
from hashlib import sha256
from typing import TypedDict

from flask import current_app
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as postgres_insert

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class FormSchemaModel(SpiffworkflowBaseDBModel):
    __tablename__ = "form_schema"

    hash: str = db.Column(db.String(255), nullable=False, unique=True, primary_key=True)
    version_control_revision: str = db.Column(db.String(255), nullable=False)
    process_model_identifier: str = db.Column(db.String(255), nullable=False, index=True)

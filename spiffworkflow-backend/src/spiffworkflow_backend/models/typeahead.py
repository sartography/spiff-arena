from dataclasses import dataclass

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class TypeaheadModel(SpiffworkflowBaseDBModel):
    __tablename__ = "typeahead"

    id: int = db.Column(db.Integer, primary_key=True)
    category: str = db.Column(db.String(255), index=True)
    search_term: str = db.Column(db.String(255), index=True)
    result: dict = db.Column(db.JSON)
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

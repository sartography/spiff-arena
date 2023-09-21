from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from typing import Any
from sqlalchemy.orm import validates
from spiffworkflow_backend.helpers.spiff_enum import SpiffEnum
from spiffworkflow_backend.models.db import db


class CacheGenerationTable(SpiffEnum):
    reference_cache = "reference_cache"


class CacheGenerationModel(SpiffworkflowBaseDBModel):
    __tablename__ = "cache_generation"

    id: int = db.Column(db.Integer, primary_key=True)
    cache_table: str = db.Column(db.String(255), index=True, nullable=False)

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

    @validates("cache_table")
    def validate_cache_table(self, key: str, value: Any) -> Any:
        return self.validate_enum_field(key, value, CacheGenerationTable)

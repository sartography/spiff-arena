from dataclasses import dataclass
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class FeatureFlagModel(SpiffworkflowBaseDBModel):
    __tablename__ = "feature_flags"

    id: int = db.Column(db.Integer, primary_key=True)
    generation_id: int = db.Column(ForeignKey(CacheGenerationModel.id), nullable=False, unique=True, index=True)  # type: ignore
    value: dict = db.Column(db.JSON, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    generation = relationship(CacheGenerationModel)

    @classmethod
    def most_recent_feature_flags(cls) -> dict[str, Any]:
        cache_generation = CacheGenerationModel.newest_generation_for_table("feature_flags")
        if cache_generation is None:
            return {}

        result = cls.query.filter_by(generation_id=cache_generation.id).first()
        return {} if result is None else result.value  # type: ignore

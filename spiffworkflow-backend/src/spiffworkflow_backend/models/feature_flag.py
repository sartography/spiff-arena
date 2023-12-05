from dataclasses import dataclass
from typing import Any

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class FeatureFlagModel(SpiffworkflowBaseDBModel):
    __tablename__ = "feature_flag"

    id: int = db.Column(db.Integer, primary_key=True)
    generation_id: int = db.Column(ForeignKey(CacheGenerationModel.id), nullable=False, unique=True, index=True)  # type: ignore
    value: dict = db.Column(db.JSON, nullable=False)
    updated_at_in_seconds: int = db.Column(db.Integer, nullable=False)
    created_at_in_seconds: int = db.Column(db.Integer, nullable=False)

    generation = relationship(CacheGenerationModel)

    @classmethod
    def most_recent_feature_flags(cls) -> dict[str, Any]:
        cache_generation = CacheGenerationModel.newest_generation_for_table(cls.__tablename__)
        if cache_generation is None:
            return {}

        result = cls.query.filter_by(generation_id=cache_generation.id).first()
        return {} if result is None else result.value  # type: ignore

    @classmethod
    def set_most_recent_feature_flags(cls, value: dict[str, Any]) -> None:
        cache_generation = CacheGenerationModel(cache_table=cls.__tablename__)
        feature_flags = FeatureFlagModel(generation=cache_generation, value=value)
        db.session.add(cache_generation)
        db.session.add(feature_flags)
        db.session.commit()

import os

from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.cache_generation import CacheGenerationModel

class ReferenceCacheService:
    @classmethod
    def upsearch(cls, location: str, identifier: str, type: str) -> str | None:
        # really want to be able to join to this table on max(id)
        cache_generation = CacheGenerationModel.newest_generation_for_table("reference_cache")
        if cache_generation is None:
            return None
        locations = cls.upsearch_locations(location)
        references = ReferenceCacheModel.query.filter_by(
            identifier=identifier,
            type=type,
            generation=cache_generation,
        ).filter(
            relative_location.in_(locations)
        ).order_by(ReferenceCacheModel.relative_location.desc()).all()

        for reference in references:
            # TODO: permissions check
            return reference
        
        return None

    @classmethod
    def upsearch_locations(cls, location: str) -> list[str]:
        locations = []

        while location != "":
            locations.append(location)
            location = os.path.dirname(location)
        
        return locations

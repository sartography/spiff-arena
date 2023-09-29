

from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel

class ReferenceCacheService:
    @classmethod
    def upsearch(cls, location: str, identifier: str, type: str) -> str | None:
        return None

    @classmethod
    def upsearch_locations(cls, location: str) -> list[str]:
        locations = [location]
        return locations

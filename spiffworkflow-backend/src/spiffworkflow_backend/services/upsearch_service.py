import os

class UpsearchService:
    @classmethod
    def upsearch_locations(cls, location: str) -> list[str]:
        locations = []

        while location != "":
            locations.append(location)
            location = os.path.dirname(location)

        return locations

    

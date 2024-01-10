import os


class UpsearchService:
    @classmethod
    def upsearch_locations(cls, process_model_identifier: str) -> list[str]:
        location = process_model_identifier
        locations = []

        while location != "":
            locations.append(location)
            location = os.path.dirname(location)

        return locations

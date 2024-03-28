import os


class UpsearchService:
    @classmethod
    def upsearch_locations(cls, process_model_identifier: str | None) -> list[str]:
        location = process_model_identifier or ""
        locations = []

        while location != "":
            locations.append(location)
            location = os.path.dirname(location)

        locations.append("")

        return locations

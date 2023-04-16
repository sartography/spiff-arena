from flask import current_app
from typing import Optional

class ElementUnitsService:
    """Feature gated glue between the backend and spiff-element-units."""

    @classmethod
    def _cache_dir(cls) -> Optional[str]:
        return current_app.config["SPIFFWORKFLOW_BACKEND_ELEMENT_UNITS_CACHE_DIR"]

    @classmethod
    def _enabled(cls) -> bool:
        enabled = current_app.config["SPIFFWORKFLOW_BACKEND_FEATURE_ELEMENT_UNITS_ENABLED"]
        return enabled and cls._cache_dir()

    @classmethod
    def cache_element_units(cls, cache_dir: str, cache_key: str, workflow_spec_json: str) -> None:
        if not cls._enabled():
            return None

        # for now we are importing inside each of these functions, not sure the best
        # way to do this in an overall feature flagged strategy but this gets things
        # moving
        import spiff_element_units

        return spiff_element_units.cache_element_units(cache_dir, cache_key, workflow_spec_json)

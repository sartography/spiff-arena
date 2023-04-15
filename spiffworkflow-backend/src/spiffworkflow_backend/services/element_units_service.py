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
        return enabled and cls._cache_dir() is not None

    @classmethod
    def cache_element_units(cls) -> None:
        if not cls._enabled():
            return None

        # for now we are importing inside each of these functions, not sure the best
        # way to do this in an overall feature flagged strategy but this gets things
        # moving
        import spiff_element_units

        current_app.logger.info(f"spiff_element_units cache @ {cls._cache_dir()}")

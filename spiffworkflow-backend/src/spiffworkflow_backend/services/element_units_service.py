import json
from typing import Optional
from typing import Dict, Any

from flask import current_app

BpmnSpecDict = Dict[str, Any]

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
    def cache_element_units(cls, cache_key: str, bpmn_spec_dict: BpmnSpecDict) -> None:
        if not cls._enabled():
            return None
        
        try:
            # for now we are importing inside each of these functions, not sure the best
            # way to do this in an overall feature flagged strategy but this gets things
            # moving
            import spiff_element_units

            bpmn_spec_json = json.dumps(bpmn_spec_dict)
            return spiff_element_units.cache_element_units(cls._cache_dir(), cache_key, bpmn_spec_json)
        except Exception as e:
            current_app.logger.exception(e)
            return None

    @classmethod
    def cached_element_unit_for_process(cls, cache_key: str, process_id: str) -> Optional[BpmnSpecDict]:
        if not cls._enabled():
            return None

        try:
            # for now we are importing inside each of these functions, not sure the best
            # way to do this in an overall feature flagged strategy but this gets things
            # moving
            import spiff_element_units

            bpmn_spec_json = spiff_element_units.cached_element_unit_for_process(cls._cache_dir(), cache_key, process_id)
            return json.loads(bpmn_spec_json)
        except Exception as e:
            current_app.logger.exception(e)
            return None

    @classmethod
    def cached_element_unit_for_element(cls, cache_key: str, process_id: str, element_id: str) -> Optional[BpmnSpecDict]:
        if not cls._enabled():
            return None

        try:
            # for now we are importing inside each of these functions, not sure the best
            # way to do this in an overall feature flagged strategy but this gets things
            # moving
            import spiff_element_units

            bpmn_spec_json = spiff_element_units.cached_element_unit_for_element(
                cls._cache_dir(), cache_key, process_id, element_id
            )
            return json.loads(bpmn_spec_json)
        except Exception as e:
            current_app.logger.exception(e)
            return None

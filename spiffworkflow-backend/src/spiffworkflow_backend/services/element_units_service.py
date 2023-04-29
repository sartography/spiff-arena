import json
from typing import Any
from typing import Dict
from typing import Optional

from flask import current_app

BpmnSpecDict = Dict[str, Any]


class ElementUnitsService:
    """Feature gated glue between the backend and spiff-element-units."""

    @classmethod
    def _cache_dir(cls) -> Optional[str]:
        return current_app.config["SPIFFWORKFLOW_BACKEND_ELEMENT_UNITS_CACHE_DIR"]  # type: ignore

    @classmethod
    def _enabled(cls) -> bool:
        enabled = current_app.config["SPIFFWORKFLOW_BACKEND_FEATURE_ELEMENT_UNITS_ENABLED"]
        return enabled and cls._cache_dir() is not None

    @classmethod
    def cache_element_units_for_workflow(cls, cache_key: str, bpmn_spec_dict: BpmnSpecDict) -> None:
        if not cls._enabled():
            return None

        try:
            # for now we are importing inside each of these functions, not sure the best
            # way to do this in an overall feature flagged strategy but this gets things
            # moving
            import spiff_element_units  # type: ignore

            bpmn_spec_json = json.dumps(bpmn_spec_dict)
            spiff_element_units.cache_element_units_for_workflow(cls._cache_dir(), cache_key, bpmn_spec_json)
        except Exception as e:
            current_app.logger.exception(e)
        return None

    @classmethod
    def workflow_from_cached_element_unit(cls, cache_key: str, process_id: str, element_id: str) -> Optional[BpmnSpecDict]:
        if not cls._enabled():
            return None

        try:
            # for now we are importing inside each of these functions, not sure the best
            # way to do this in an overall feature flagged strategy but this gets things
            # moving
            import spiff_element_units

            bpmn_spec_json = spiff_element_units.workflow_from_cached_element_unit(
                cls._cache_dir(), cache_key, process_id, element_id
            )
            return json.loads(bpmn_spec_json)  # type: ignore
        except Exception as e:
            current_app.logger.exception(e)
            return None

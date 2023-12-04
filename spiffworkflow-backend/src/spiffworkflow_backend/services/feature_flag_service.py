from typing import Any

from flask import current_app
from flask import g

from spiffworkflow_backend.models.feature_flag import FeatureFlagModel

GLOBAL_FEATURE_FLAGS = "__spiff_global_feature_flags"


class FeatureFlagService:
    @classmethod
    def _process_model_specific_value(cls, name: str, feature_flags: dict[str, Any]) -> bool | None:
        tld = current_app.config.get("THREAD_LOCAL_DATA")

        if not tld or not hasattr(tld, "process_model_identifier"):
            return None

        return feature_flags.get(tld.process_model_identifier, {}).get(name)  # type: ignore

    @classmethod
    def feature_enabled(cls, name: str, enabled_by_default: bool = False) -> bool:
        if not hasattr(g, "feature_flags"):
            # TODO: add a script so a process model would set this, below is just an example
            feature_flags_example = {
                "misc/jonjon/lazy-call-activity/sample1": {
                    "element_units": False,
                },
                GLOBAL_FEATURE_FLAGS: {
                    "element_units": False,
                },
            }
            FeatureFlagModel.set_most_recent_feature_flags(feature_flags_example)
            g.feature_flags = FeatureFlagModel.most_recent_feature_flags()

        value = cls._process_model_specific_value(name, g.feature_flags)
        if value is not None:
            return value

        return g.feature_flags.get(GLOBAL_FEATURE_FLAGS, {}).get(name, enabled_by_default)  # type: ignore

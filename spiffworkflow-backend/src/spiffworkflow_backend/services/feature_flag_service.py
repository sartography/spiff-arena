from typing import Any

from flask import current_app
from flask import g

from spiffworkflow_backend.models.feature_flag import FeatureFlagModel

DEFAULT_FEATURE_FLAGS = "__spiff_default_feature_flags"


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
            g.feature_flags = FeatureFlagModel.most_recent_feature_flags()

        value = cls._process_model_specific_value(name, g.feature_flags)
        if value is not None:
            return value

        return g.feature_flags.get(DEFAULT_FEATURE_FLAGS, {}).get(name, enabled_by_default)  # type: ignore

    @classmethod
    def set_feature_flags(cls, default_feature_flags: dict[str, Any], process_model_overrides: dict[str, Any]) -> None:
        feature_flags = {}
        feature_flags.update(process_model_overrides)
        feature_flags[DEFAULT_FEATURE_FLAGS] = default_feature_flags
        FeatureFlagModel.set_most_recent_feature_flags(feature_flags)

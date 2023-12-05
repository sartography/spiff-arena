from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.feature_flag_service import FeatureFlagService


class SetFeatureFlags(Script):
    def get_description(self) -> str:
        return """Allows updating default and process model specific feature flags."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        default_feature_flags = args[0]
        process_model_overrides = args[1]
        return FeatureFlagService.set_feature_flags(default_feature_flags, process_model_overrides)


class FeatureFlagService:

    @staticmethod
    def feature_enabled(name: str, enabled_by_default: bool = False) -> bool:
        return False

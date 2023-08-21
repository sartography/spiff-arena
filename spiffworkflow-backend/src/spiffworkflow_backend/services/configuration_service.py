import json
from typing import Any

from spiffworkflow_backend.models.configuration import ConfigurationModel
from spiffworkflow_backend.models.db import db


class ConfigurationService:
    @staticmethod
    def configuration_for_category(category: str) -> Any:
        config = db.session.query(ConfigurationModel).filter(ConfigurationModel.category == category).first()
        try:
            value = config.value if config is not None else ""
            return json.loads(value)  # type: ignore
        except Exception:
            return {}

    @staticmethod
    def update_configuration_for_category(category: str, new_config: dict[str, Any]) -> None:
        config = db.session.query(ConfigurationModel).filter(ConfigurationModel.category == category).first()
        if config is None:
            config = ConfigurationModel(category=category)
        if "value" in new_config:
            config.value = new_config["value"]
        else:
            config.value = {}

        db.session.add(config)
        db.session.commit()

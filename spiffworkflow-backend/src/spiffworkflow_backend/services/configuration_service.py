from spiffworkflow_backend.models.db import db
from typing import Any
from spiffworkflow_backend.models.configuration import ConfigurationModel
import json

class ConfigurationService:

    @staticmethod
    def configuration_for_category(category: str) -> dict[str, Any]:
        config = db.session.query(ConfigurationModel).filter(ConfigurationModel.category == category).first()
        if config is None:
            return {}
        return json.loads(config.value)

    @staticmethod
    def update_configuration_for_category(category: str, new_config: dict[str, Any]):
        config = db.session.query(ConfigurationModel).filter(ConfigurationModel.category == category).first()
        if config is None:
            config = ConfigurationModel(category=category)
        if "value" in new_config:
            config.value = new_config["value"]
        else:
            config.value = {}
        
        db.session.add(config)
        db.session.commit()

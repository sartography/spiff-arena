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
        return json.loads(config)
    
# {
#             "github": {
#                 "consumer_key": "SPIFF_SECRET:GITHUB_CONSUMER_KEY",
#                 "consumer_secret": "SPIFF_SECRET:GITHUB_CONSUMER_SECRET",
#                 "request_token_params": {"scope": "user:email"},
#                 "base_url": "https://api.github.com/",
#                 "request_token_url": None,
#                 "access_token_method": "POST",
#                 "access_token_url": "https://github.com/login/oauth/access_token",
#                 "authorize_url": "https://github.com/login/oauth/authorize",
#             },
#         }

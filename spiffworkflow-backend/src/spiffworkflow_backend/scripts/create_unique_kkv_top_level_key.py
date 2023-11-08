from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel

class CreateUniqueKKVTopLevelKey(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return (
            "Creates a new unique KKV top level key using the provided prefix. "
            "This allows for a safe construction of incrementing keys, such as study1, study2."
        )

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        top_level_key_prefix = args[0]

        model = KKVDataStoreModel(top_level_key="", secondary_key="", value="")
        db.session.add(model)
        db.session.commit()
        
        top_level_key = f"{top_level_key_prefix}{model.id}"

        db.session.delete(model)
        db.session.commit()

        return top_level_key

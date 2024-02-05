from typing import Any

from spiffworkflow_backend.data_stores.crud import DataStoreCRUD
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.kkv_data_store import KKVDataStoreModel
from spiffworkflow_backend.models.kkv_data_store_entry import KKVDataStoreEntryModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


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
        identifier = args[0]
        top_level_key_prefix = args[1]
        spiff_task = script_attributes_context.task
        location: str | None = None

        if identifier is not None and spiff_task is not None:
            location = DataStoreCRUD.data_store_location_for_task(KKVDataStoreModel, spiff_task, identifier)

        store_model: KKVDataStoreModel | None = None

        if location is not None:
            store_model = db.session.query(KKVDataStoreModel).filter_by(identifier=identifier, location=location).first()

        if store_model is None:
            raise Exception(f"Could not find KKV data store with the identifier '{identifier}'")

        model = KKVDataStoreEntryModel(kkv_data_store_id=store_model.id, top_level_key="", secondary_key="", value={})
        db.session.add(model)
        db.session.commit()

        top_level_key = f"{top_level_key_prefix}{model.id}"

        db.session.delete(model)
        db.session.commit()

        return top_level_key

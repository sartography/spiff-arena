from typing import Any

from flask import g
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user_property import UserPropertyModel
from spiffworkflow_backend.scripts.script import InvalidArgsGivenToScriptError
from spiffworkflow_backend.scripts.script import Script


class SetUserProperties(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Sets given user properties on current user."""

    def run(self, script_attributes_context: ScriptAttributesContext, *args: Any, **kwargs: Any) -> Any:
        properties = args[0]
        if not isinstance(properties, dict):
            raise InvalidArgsGivenToScriptError(f"Args to set_user_properties must be a dict. '{properties}' is invalid.")
        # consider using engine-specific insert or update metaphor in future: https://stackoverflow.com/a/68431412/6090676
        for property_key, property_value in properties.items():
            user_property = UserPropertyModel.query.filter_by(user_id=g.user.id, key=property_key).first()
            if user_property is None:
                user_property = UserPropertyModel(
                    user_id=g.user.id,
                    key=property_key,
                )
            user_property.value = property_value
            db.session.add(user_property)
            db.session.commit()

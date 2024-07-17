from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class FormSchemaModel(SpiffworkflowBaseDBModel):
    __tablename__ = "form_schema"

    hash: str = db.Column(db.String(255), primary_key=True)
    version_control_revision: str = db.Column(db.String(255), primary_key=True)
    process_model_identifier: str = db.Column(db.String(255), primary_key=True)

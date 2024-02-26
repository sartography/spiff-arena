from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


class MessageTriggerableProcessModel(SpiffworkflowBaseDBModel):
    __tablename__ = "message_triggerable_process_model"

    id = db.Column(db.Integer, primary_key=True)
    message_name: str = db.Column(db.String(255), index=True)
    process_model_identifier: str = db.Column(db.String(255), nullable=False, index=True)
    file_name: str = db.Column(db.String(255), index=True)

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

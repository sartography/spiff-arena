"""Data_store."""
from flask_bpmn.models.db import db
from flask_bpmn.models.db import SpiffworkflowBaseDBModel
from flask_marshmallow.sqla import SQLAlchemyAutoSchema  # type: ignore


class DataStoreModel(SpiffworkflowBaseDBModel):
    """DataStoreModel."""

    __tablename__ = "data_store"
    id = db.Column(db.Integer, primary_key=True)
    updated_at_in_seconds = db.Column(db.Integer)
    key = db.Column(db.String(50), nullable=False)
    process_instance_id = db.Column(db.Integer)
    task_spec = db.Column(db.String(50))
    spec_id = db.Column(db.String(50))
    user_id = db.Column(db.String(50), nullable=True)
    file_id = db.Column(db.Integer, db.ForeignKey("file.id"), nullable=True)
    value = db.Column(db.String(50))


class DataStoreSchema(SQLAlchemyAutoSchema):  # type: ignore
    """DataStoreSchema."""

    class Meta:
        """Meta."""

        model = DataStoreModel
        load_instance = True
        include_fk = True
        sqla_session = db.session

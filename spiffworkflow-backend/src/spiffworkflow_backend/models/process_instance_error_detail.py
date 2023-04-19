from dataclasses import dataclass
from sqlalchemy.orm import relationship
from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from sqlalchemy import ForeignKey
from spiffworkflow_backend.models.db import db


@dataclass
class ProcessInstanceErrorDetailModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_error_detail"
    id: int = db.Column(db.Integer, primary_key=True)

    process_instance_event_id: int = db.Column(ForeignKey("process_instance_event.id"), nullable=False, index=True)
    process_instance_event = relationship('ProcessInstanceEventModel')

    message: str = db.Column(db.String(1024), nullable=False)

    # this should be 65k in mysql
    stacktrace: str = db.Column(db.Text(), nullable=False)

from dataclasses import dataclass
from typing import Optional

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db


@dataclass
class ProcessInstanceErrorDetailModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_error_detail"
    id: int = db.Column(db.Integer, primary_key=True)

    process_instance_event_id: int = db.Column(ForeignKey("process_instance_event.id"), nullable=False, index=True)
    process_instance_event = relationship("ProcessInstanceEventModel")  # type: ignore

    message: str = db.Column(db.String(1024), nullable=False)

    # this should be 65k in mysql
    stacktrace: Optional[list] = db.Column(db.JSON, nullable=False)

    task_line_number: Optional[int] = db.Column(db.Integer)
    task_offset: Optional[int] = db.Column(db.Integer)
    task_line_contents: Optional[str] = db.Column(db.String(255))
    task_trace: Optional[list] = db.Column(db.JSON)

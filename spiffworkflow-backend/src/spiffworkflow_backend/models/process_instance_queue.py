from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class ProcessInstanceQueueModel(SpiffworkflowBaseDBModel):
    __tablename__ = "process_instance_queue"

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), unique=True, nullable=False)  # type: ignore
    priority: int = db.Column(db.Integer)
    locked_by: str | None = db.Column(db.String(80), index=True, nullable=True)
    locked_at_in_seconds: int | None = db.Column(db.Integer, index=True, nullable=True)
    status: str = db.Column(db.String(50), index=True)

    # for timers. right now the apscheduler jobs without celery check for waiting process instances.
    # if the instance's run_at_in_seconds is now or earlier, the instance will run.
    # so we can save some effort if we detect that it is scheduled to run later.
    # note that we still run an apscheduler job to manage timer start events, even if
    # SPIFFWORKFLOW_BACKEND_CELERY_ENABLED=true
    run_at_in_seconds: int = db.Column(db.Integer)

    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)

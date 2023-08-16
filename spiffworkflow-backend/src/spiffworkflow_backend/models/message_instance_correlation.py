from dataclasses import dataclass

from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel


@dataclass
class MessageInstanceCorrelationRuleModel(SpiffworkflowBaseDBModel):
    """These are the correlations of a specific Message Instance.

    These will only exist on receive messages. It provides the expression to run on
    a send messages payload which must match receive messages correlation_key dictionary
     to be considered a valid match.  If the expected value is null, then it does not need to
    match, but the expression should still evaluate and produce a result.
    """

    __tablename__ = "message_instance_correlation_rule"
    __table_args__ = (
        db.UniqueConstraint(
            "message_instance_id",
            "name",
            name="message_instance_id_name_unique",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    message_instance_id = db.Column(ForeignKey(MessageInstanceModel.id), nullable=False, index=True)  # type: ignore

    name: str = db.Column(db.String(50), nullable=False, index=True)
    retrieval_expression: str = db.Column(db.String(255))
    updated_at_in_seconds: int = db.Column(db.Integer)
    created_at_in_seconds: int = db.Column(db.Integer)
    correlation_key_names: list = db.Column(db.JSON)

    message_instance = relationship("MessageInstanceModel", back_populates="correlation_rules")

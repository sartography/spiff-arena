"""Message_correlation_message_instance."""

from sqlalchemy import ForeignKey
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel

message_correlation_message_instance_table \
    = db.Table('message_correlation_message_instance',
               db.Column('message_instance_id',
                         ForeignKey('message_instance.id'), primary_key=True),
               db.Column('message_correlation_id',
                         ForeignKey('message_correlation.id'),primary_key=True),
               )
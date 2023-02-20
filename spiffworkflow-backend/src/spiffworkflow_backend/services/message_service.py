"""Message_service."""
from typing import Any
from typing import Optional

from sqlalchemy import and_
from sqlalchemy import or_
from sqlalchemy import select

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_correlation import MessageCorrelationModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel, MessageStatuses
from spiffworkflow_backend.models.message_triggerable_process_model import (
    MessageTriggerableProcessModel,
)
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class MessageServiceError(Exception):
    """MessageServiceError."""


class MessageService:
    """MessageService."""

    @classmethod
    def process_message_instances(cls) -> None:
        """Process_message_instances."""
        message_instances_send = MessageInstanceModel.query.filter_by(
            message_type="send", status="ready"
        ).all()
        message_instances_receive = MessageInstanceModel.query.filter_by(
            message_type="receive", status="ready"
        ).all()

        for message_instance_send in message_instances_send:
            # check again in case another background process picked up the message
            # while the previous one was running
            if message_instance_send.status != "ready":
                continue

            message_instance_send.status = "running"
            db.session.add(message_instance_send)
            db.session.commit()

            message_instance_receive = None
            try:
                message_instance_receive = cls.get_message_instance_receive(
                    message_instance_send, message_instances_receive
                )
                if message_instance_receive is None:
                    message_triggerable_process_model = (
                        MessageTriggerableProcessModel.query.filter_by(
                            message_model_id=message_instance_send.message_model_id
                        ).first()
                    )
                    if message_triggerable_process_model:
                        process_instance_send = ProcessInstanceModel.query.filter_by(
                            id=message_instance_send.process_instance_id,
                        ).first()
                        # TODO: use the correct swimlane user when that is set up
                        cls.process_message_triggerable_process_model(
                            message_triggerable_process_model,
                            message_instance_send.message_model.name,
                            message_instance_send.payload,
                            process_instance_send.process_initiator,
                        )
                        message_instance_send.status = "completed"
                    else:
                        # if we can't get a queued message then put it back in the queue
                        message_instance_send.status = "ready"

                else:
                    if message_instance_receive.status != "ready":
                        continue
                    message_instance_receive.status = "running"

                    cls.process_message_receive(
                        message_instance_receive,
                        message_instance_send.message_model.name,
                        message_instance_send.payload,
                    )
                    message_instance_receive.status = "completed"
                    db.session.add(message_instance_receive)
                    message_instance_send.status = "completed"

                db.session.add(message_instance_send)
                db.session.commit()
            except Exception as exception:
                db.session.rollback()
                message_instance_send.status = "failed"
                message_instance_send.failure_cause = str(exception)
                db.session.add(message_instance_send)

                if message_instance_receive:
                    message_instance_receive.status = "failed"
                    message_instance_receive.failure_cause = str(exception)
                    db.session.add(message_instance_receive)

                db.session.commit()
                raise exception

    @staticmethod
    def process_message_triggerable_process_model(
        message_triggerable_process_model: MessageTriggerableProcessModel,
        message_model_name: str,
        message_payload: dict,
        user: UserModel,
    ) -> ProcessInstanceModel:
        """Process_message_triggerable_process_model."""
        process_instance_receive = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            message_triggerable_process_model.process_model_identifier,
            user,
        )
        processor_receive = ProcessInstanceProcessor(process_instance_receive)
        processor_receive.do_engine_steps(save=False)
        processor_receive.bpmn_process_instance.catch_bpmn_message(
            message_model_name,
            message_payload
        )
        processor_receive.do_engine_steps(save=True)

        return process_instance_receive

    @staticmethod
    def process_message_receive(
        message_instance_receive: MessageInstanceModel,
        message_model_name: str,
        message_payload: dict,
    ) -> None:
        """Process_message_receive."""
        process_instance_receive = ProcessInstanceModel.query.filter_by(
            id=message_instance_receive.process_instance_id
        ).first()
        if process_instance_receive is None:
            raise MessageServiceError(
                (
                    (
                        "Process instance cannot be found for queued message:"
                        f" {message_instance_receive.id}.Tried with id"
                        f" {message_instance_receive.process_instance_id}"
                    ),
                )
            )


        processor_receive = ProcessInstanceProcessor(process_instance_receive)
        processor_receive.bpmn_process_instance.catch_bpmn_message(
            message_model_name,
            message_payload,
            correlations=message_instance_receive.correlation_dictionary(),
        )
        processor_receive.do_engine_steps(save=True)
        message_instance_receive.status = MessageStatuses.completed.value
        db.session.add(message_instance_receive)
        db.session.commit()

    @staticmethod
    def get_message_instance_receive(
        message_instance_send: MessageInstanceModel,
        message_instances_receive: list[MessageInstanceModel],
    ) -> Optional[MessageInstanceModel]:
        """Returns the message instance that correlates to the send message, or None if nothing correlates."""
        for message_instance in message_instances_receive:
            if message_instance.correlates(message_instance_send):
                return message_instance
        return None

    @staticmethod
    def get_process_instance_for_message_instance(
        message_instance: MessageInstanceModel,
    ) -> Any:
        """Get_process_instance_for_message_instance."""
        process_instance = ProcessInstanceModel.query.filter_by(
            id=message_instance.process_instance_id
        ).first()
        if process_instance is None:
            raise MessageServiceError(
                f"Process instance cannot be found for message: {message_instance.id}."
                f"Tried with id {message_instance.process_instance_id}"
            )

        return process_instance

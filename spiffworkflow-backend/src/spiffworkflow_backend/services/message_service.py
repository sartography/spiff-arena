import os

from SpiffWorkflow.bpmn import BpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.message import CorrelationProperty  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins import StartEventMixin  # type: ignore
from SpiffWorkflow.spiff.specs.event_definitions import MessageEventDefinition  # type: ignore

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.helpers.spiff_enum import ProcessInstanceExecutionMode
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_instance import MessageStatuses
from spiffworkflow_backend.models.message_instance import MessageTypes
from spiffworkflow_backend.models.message_triggerable_process_model import MessageTriggerableProcessModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import CustomBpmnScriptEngine
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.user_service import UserService


class MessageServiceError(Exception):
    pass


class MessageService:
    @classmethod
    def correlate_send_message(
        cls,
        message_instance_send: MessageInstanceModel,
        execution_mode: str | None = None,
    ) -> MessageInstanceModel | None:
        """Connects the given send message to a 'receive' message if possible.

        :param message_instance_send:
        :return: the message instance that received this message.
        """
        # Thread safe via db locking - don't try to progress the same send message over multiple instances
        if message_instance_send.status != MessageStatuses.ready.value:
            return None
        message_instance_send.status = MessageStatuses.running.value
        db.session.add(message_instance_send)
        db.session.commit()

        # Find available messages that might match
        available_receive_messages = MessageInstanceModel.query.filter_by(
            name=message_instance_send.name,
            status=MessageStatuses.ready.value,
            message_type=MessageTypes.receive.value,
        ).all()
        message_instance_receive: MessageInstanceModel | None = None
        try:
            for message_instance in available_receive_messages:
                if message_instance.correlates(message_instance_send, CustomBpmnScriptEngine()):
                    message_instance_receive = message_instance

            if message_instance_receive is None:
                # Check for a message triggerable process and start that to create a new message_instance_receive
                message_triggerable_process_model = MessageTriggerableProcessModel.query.filter_by(
                    message_name=message_instance_send.name
                ).first()
                if message_triggerable_process_model:
                    user: UserModel | None = message_instance_send.user
                    if user is None:
                        user = UserService.find_or_create_system_user()
                    receiving_process = MessageService.start_process_with_message(
                        message_triggerable_process_model, user, execution_mode=execution_mode
                    )
                    message_instance_receive = MessageInstanceModel.query.filter_by(
                        process_instance_id=receiving_process.id,
                        message_type="receive",
                        status="ready",
                    ).first()
            else:
                receiving_process = MessageService.get_process_instance_for_message_instance(message_instance_receive)

            # Assure we can send the message, otherwise keep going.
            if message_instance_receive is None or not receiving_process.can_receive_message():
                message_instance_send.status = "ready"
                message_instance_send.status = "ready"
                db.session.add(message_instance_send)
                db.session.commit()
                return None

            # Set the receiving message to running, so it is not altered elswhere ...
            message_instance_receive.status = "running"

            cls.process_message_receive(
                receiving_process,
                message_instance_receive,
                message_instance_send,
            )
            message_instance_receive.status = "completed"
            message_instance_receive.counterpart_id = message_instance_send.id
            db.session.add(message_instance_receive)
            message_instance_send.status = "completed"
            message_instance_send.counterpart_id = message_instance_receive.id
            db.session.add(message_instance_send)
            db.session.commit()
            return message_instance_receive

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

    @classmethod
    def correlate_all_message_instances(cls) -> None:
        """Look at ALL the Send and Receive Messages and attempt to find correlations."""
        message_instances_send = MessageInstanceModel.query.filter_by(message_type="send", status="ready").all()

        for message_instance_send in message_instances_send:
            cls.correlate_send_message(message_instance_send)

    @classmethod
    def start_process_with_message(
        cls,
        message_triggerable_process_model: MessageTriggerableProcessModel,
        user: UserModel,
        execution_mode: str | None = None,
    ) -> ProcessInstanceModel:
        """Start up a process instance, so it is ready to catch the event."""
        if os.environ.get("SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER") == "true":
            raise MessageServiceError(
                "Calling start_process_with_message in a celery worker. This is not supported! (We may need to add"
                " additional_processing_identifier to this code path."
            )

        process_instance_receive = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            message_triggerable_process_model.process_model_identifier,
            user,
        )
        with ProcessInstanceQueueService.dequeued(process_instance_receive):
            processor_receive = ProcessInstanceProcessor(process_instance_receive)
            cls._cancel_non_matching_start_events(processor_receive, message_triggerable_process_model)
            processor_receive.save()

        if not queue_process_instance_if_appropriate(
            process_instance_receive, execution_mode=execution_mode
        ) and not ProcessInstanceQueueService.is_enqueued_to_run_in_the_future(process_instance_receive):
            execution_strategy_name = None
            if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
                execution_strategy_name = "greedy"
            processor_receive.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name)

        return process_instance_receive

    @classmethod
    def _cancel_non_matching_start_events(
        cls, processor_receive: ProcessInstanceProcessor, message_triggerable_process_model: MessageTriggerableProcessModel
    ) -> None:
        """Cancel any start event that does not match the start event that triggered this.

        After that SpiffWorkflow and the WorkflowExecutionService can figure it out.
        """
        start_tasks = processor_receive.bpmn_process_instance.get_tasks(spec_class=StartEventMixin)
        for start_task in start_tasks:
            if not isinstance(start_task.task_spec.event_definition, MessageEventDefinition):
                start_task.cancel()
            elif start_task.task_spec.event_definition.name != message_triggerable_process_model.message_name:
                start_task.cancel()

    @staticmethod
    def get_process_instance_for_message_instance(
        message_instance_receive: MessageInstanceModel,
    ) -> ProcessInstanceModel:
        process_instance_receive: ProcessInstanceModel = ProcessInstanceModel.query.filter_by(
            id=message_instance_receive.process_instance_id
        ).first()
        if process_instance_receive is None:
            raise MessageServiceError(
                (
                    (
                        "Process instance cannot be found for queued message:"
                        f" {message_instance_receive.id}. Tried with id"
                        f" {message_instance_receive.process_instance_id}"
                    ),
                )
            )
        return process_instance_receive

    @staticmethod
    def process_message_receive(
        process_instance_receive: ProcessInstanceModel,
        message_instance_receive: MessageInstanceModel,
        message_instance_send: MessageInstanceModel,
    ) -> None:
        correlation_properties = []
        for cr in message_instance_receive.correlation_rules:
            correlation_properties.append(
                CorrelationProperty(
                    name=cr.name,
                    retrieval_expression=cr.retrieval_expression,
                    correlation_keys=cr.correlation_key_names,
                )
            )
        bpmn_message = MessageEventDefinition(
            name=message_instance_send.name,
            correlation_properties=correlation_properties,
        )
        bpmn_event = BpmnEvent(
            event_definition=bpmn_message,
            payload=message_instance_send.payload,
            correlations=message_instance_send.correlation_keys,
        )
        processor_receive = ProcessInstanceProcessor(process_instance_receive)
        processor_receive.bpmn_process_instance.send_event(bpmn_event)
        processor_receive.do_engine_steps(save=True)
        message_instance_receive.status = MessageStatuses.completed.value
        db.session.add(message_instance_receive)
        db.session.commit()

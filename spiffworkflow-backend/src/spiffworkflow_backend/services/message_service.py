from typing import Any

from flask import current_app
from flask import g
from SpiffWorkflow.bpmn import BpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.message import CorrelationProperty  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins import StartEventMixin  # type: ignore
from SpiffWorkflow.spiff.specs.event_definitions import MessageEventDefinition  # type: ignore

from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import (
    queue_process_instance_if_appropriate,
)
from spiffworkflow_backend.background_processing.celery_tasks.process_instance_task_producer import should_queue_process_instance
from spiffworkflow_backend.exceptions.api_error import ApiError
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
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceIsAlreadyLockedError
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_instance_tmp_service import ProcessInstanceTmpService
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
                    receiving_process_instance = MessageService.start_process_with_message(
                        message_triggerable_process_model,
                        user,
                        message_instance_send=message_instance_send,
                        execution_mode=execution_mode,
                    )
                    message_instance_receive = MessageInstanceModel.query.filter_by(
                        process_instance_id=receiving_process_instance.id,
                        message_type="receive",
                        status="ready",
                    ).first()
            else:
                receiving_process_instance = MessageService.get_process_instance_for_message_instance(message_instance_receive)

            # Assure we can send the message, otherwise keep going.
            if message_instance_receive is None or not receiving_process_instance.can_receive_message():
                message_instance_send.status = "ready"
                db.session.add(message_instance_send)
                db.session.commit()
                return None

            try:
                with ProcessInstanceQueueService.dequeued(receiving_process_instance):
                    # Set the receiving message to running, so it is not altered elswhere ...
                    message_instance_receive.status = "running"

                    cls.process_message_receive(
                        receiving_process_instance, message_instance_receive, message_instance_send, execution_mode=execution_mode
                    )
                    message_instance_receive.status = "completed"
                    message_instance_receive.counterpart_id = message_instance_send.id
                    db.session.add(message_instance_receive)
                    message_instance_send.status = "completed"
                    message_instance_send.counterpart_id = message_instance_receive.id
                    db.session.add(message_instance_send)
                    db.session.commit()
                if should_queue_process_instance(receiving_process_instance, execution_mode=execution_mode):
                    queue_process_instance_if_appropriate(receiving_process_instance, execution_mode=execution_mode)
                return message_instance_receive

            except ProcessInstanceIsAlreadyLockedError:
                message_instance_send.status = "ready"
                db.session.add(message_instance_send)
                db.session.commit()
                return None

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
    def correlate_all_message_instances(
        cls,
        execution_mode: str | None = None,
    ) -> None:
        """Look at ALL the Send and Receive Messages and attempt to find correlations."""
        message_instances_send = MessageInstanceModel.query.filter_by(message_type="send", status="ready").all()

        for message_instance_send in message_instances_send:
            current_app.logger.info(
                f"Processor waiting send messages: Processing message id {message_instance_send.id}. "
                f"Name: '{message_instance_send.name}'"
            )
            cls.correlate_send_message(message_instance_send, execution_mode=execution_mode)

    @classmethod
    def start_process_with_message(
        cls,
        message_triggerable_process_model: MessageTriggerableProcessModel,
        user: UserModel,
        message_instance_send: MessageInstanceModel | None = None,
        execution_mode: str | None = None,
    ) -> ProcessInstanceModel:
        """Start up a process instance, so it is ready to catch the event."""
        receiving_process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
            message_triggerable_process_model.process_model_identifier,
            user,
        )
        with ProcessInstanceQueueService.dequeued(receiving_process_instance):
            processor_receive = ProcessInstanceProcessor(receiving_process_instance)
            cls._cancel_non_matching_start_events(processor_receive, message_triggerable_process_model)
            processor_receive.save()

        execution_strategy_name = None
        if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
            execution_strategy_name = "greedy"

        # add correlations to bpmn_process_instance if not set already so we can use them in the receive message instance later.
        # these should never be set at this point but check just in case.
        if (
            message_instance_send
            and message_instance_send.correlation_keys
            and not processor_receive.bpmn_process_instance.correlations
        ):
            processor_receive.bpmn_process_instance.correlations = message_instance_send.correlation_keys

        processor_receive.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name)

        return receiving_process_instance

    @staticmethod
    def process_message_receive(
        receiving_process_instance: ProcessInstanceModel,
        message_instance_receive: MessageInstanceModel,
        message_instance_send: MessageInstanceModel,
        execution_mode: str | None = None,
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
        processor_receive = ProcessInstanceProcessor(receiving_process_instance)
        processor_receive.bpmn_process_instance.send_event(bpmn_event)
        execution_strategy_name = None

        if should_queue_process_instance(receiving_process_instance, execution_mode=execution_mode):
            # even if we are queueing, we ran a "send_event" call up above, and it updated some tasks.
            # we need to serialize these task updates to the db. do_engine_steps with save does that.
            processor_receive.do_engine_steps(save=True, execution_strategy_name="run_current_ready_tasks")
        elif not ProcessInstanceTmpService.is_enqueued_to_run_in_the_future(receiving_process_instance):
            execution_strategy_name = None
            if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
                execution_strategy_name = "greedy"
            processor_receive.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name)
        message_instance_receive.status = MessageStatuses.completed.value
        db.session.add(message_instance_receive)
        db.session.commit()

    @classmethod
    def find_message_triggerable_process_model(cls, modified_message_name: str) -> MessageTriggerableProcessModel:
        message_name, process_group_identifier = MessageInstanceModel.split_modified_message_name(modified_message_name)
        potential_matches = MessageTriggerableProcessModel.query.filter_by(message_name=message_name).all()
        actual_matches = []
        for potential_match in potential_matches:
            pgi, _ = potential_match.process_model_identifier.rsplit("/", 1)
            if pgi.startswith(process_group_identifier):
                actual_matches.append(potential_match)

        if len(actual_matches) == 0:
            raise (
                ApiError(
                    error_code="message_triggerable_process_model_not_found",
                    message=(
                        f"Could not find a message triggerable process model for {modified_message_name} in the scope of group"
                        f" {process_group_identifier}"
                    ),
                    status_code=400,
                )
            )

        if len(actual_matches) > 1:
            message_names = [f"{m.process_model_identifier} - {m.message_name}" for m in actual_matches]
            raise (
                ApiError(
                    error_code="multiple_message_triggerable_process_models_found",
                    message=f"Found {len(actual_matches)}. Expected 1. Found entries: {message_names}",
                    status_code=400,
                )
            )
        mtp: MessageTriggerableProcessModel = actual_matches[0]
        return mtp

    @classmethod
    def run_process_model_from_message(
        cls,
        modified_message_name: str,
        body: dict[str, Any],
        execution_mode: str | None = None,
    ) -> MessageInstanceModel:
        message_name, _process_group_identifier = MessageInstanceModel.split_modified_message_name(modified_message_name)

        # Create the send message
        # TODO: support the full message id - including process group - in message instance
        message_instance = MessageInstanceModel(
            message_type="send",
            name=message_name,
            payload=body,
            user_id=g.user.id,
        )
        db.session.add(message_instance)
        db.session.commit()
        try:
            receiver_message = cls.correlate_send_message(message_instance, execution_mode=execution_mode)
        except Exception as e:
            db.session.delete(message_instance)
            db.session.commit()
            raise e
        if not receiver_message:
            db.session.delete(message_instance)
            db.session.commit()
            raise (
                ApiError(
                    error_code="message_not_accepted",
                    message=(
                        "No running process instances correlate with the given message"
                        f" name of '{modified_message_name}'.  And this message name is not"
                        " currently associated with any process Start Event. Nothing"
                        " to do."
                    ),
                    status_code=400,
                )
            )
        return receiver_message

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
        receiving_process_instance: ProcessInstanceModel = ProcessInstanceModel.query.filter_by(
            id=message_instance_receive.process_instance_id
        ).first()
        if receiving_process_instance is None:
            raise MessageServiceError(
                (
                    (
                        "Process instance cannot be found for queued message:"
                        f" {message_instance_receive.id}. Tried with id"
                        f" {message_instance_receive.process_instance_id}"
                    ),
                )
            )
        return receiving_process_instance

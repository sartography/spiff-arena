import contextlib
import time
from collections.abc import Generator
from collections.abc import Iterable
from typing import Any
from typing import NoReturn
from typing import cast
from uuid import UUID

from flask import current_app
from flask import g
from SpiffWorkflow.bpmn import BpmnEvent  # type: ignore
from SpiffWorkflow.bpmn.specs.event_definitions.message import CorrelationProperty  # type: ignore
from SpiffWorkflow.bpmn.specs.mixins import StartEventMixin  # type: ignore
from SpiffWorkflow.exceptions import SpiffWorkflowException  # type: ignore
from SpiffWorkflow.spiff.specs.event_definitions import MessageEventDefinition  # type: ignore
from sqlalchemy.orm import selectinload

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
from spiffworkflow_backend.services.error_handling_service import ErrorHandlingService
from spiffworkflow_backend.services.message_instrumentation_service import MessageSendInstrumentation
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
    MAX_TIME_TO_LIVE_SECONDS = 300

    @classmethod
    def current_time_in_seconds(cls) -> int:
        return round(time.time())

    @classmethod
    def _validated_message_instance_uuid(cls, message_instance_uuid: str | None) -> str | None:
        if message_instance_uuid is None:
            return None
        if len(message_instance_uuid) > 40:
            raise ApiError(
                error_code="invalid_message_instance_uuid",
                message="message_instance_uuid must be 40 characters or fewer.",
                status_code=400,
            )
        try:
            parsed_uuid = UUID(message_instance_uuid)
        except ValueError as exception:
            raise ApiError(
                error_code="invalid_message_instance_uuid",
                message="message_instance_uuid must be a valid UUID.",
                status_code=400,
            ) from exception
        if str(parsed_uuid) != message_instance_uuid.lower():
            raise ApiError(
                error_code="invalid_message_instance_uuid",
                message="message_instance_uuid must be a valid UUID.",
                status_code=400,
            )
        return str(parsed_uuid)

    @classmethod
    def _validated_time_to_live(
        cls,
        time_to_live_in_seconds: int | None,
        message_instance_uuid: str | None,
    ) -> int:
        ttl = time_to_live_in_seconds or 0
        if ttl < 0:
            raise ApiError(
                error_code="invalid_time_to_live",
                message="time_to_live_in_seconds must be greater than or equal to 0.",
                status_code=400,
            )
        if ttl > cls.MAX_TIME_TO_LIVE_SECONDS:
            raise ApiError(
                error_code="invalid_time_to_live",
                message=f"time_to_live_in_seconds must be less than or equal to {cls.MAX_TIME_TO_LIVE_SECONDS}.",
                status_code=400,
            )
        if ttl > 0 and not message_instance_uuid:
            raise ApiError(
                error_code="message_instance_uuid_required",
                message="message_instance_uuid is required when time_to_live_in_seconds is greater than 0.",
                status_code=400,
            )
        return ttl

    @classmethod
    def _find_message_with_uuid(
        cls,
        message_instance_uuid: str | None,
    ) -> MessageInstanceModel | None:
        if not message_instance_uuid:
            return None
        return cast(
            MessageInstanceModel | None,
            MessageInstanceModel.query.filter_by(
                message_type=MessageTypes.send.value,
                message_instance_uuid=message_instance_uuid,
            )
            .order_by(MessageInstanceModel.id)
            .first(),
        )

    @classmethod
    def expire_ready_send_messages(cls, now_in_seconds: int | None = None, commit: bool = True) -> None:
        now = now_in_seconds if now_in_seconds is not None else cls.current_time_in_seconds()
        expired_messages = (
            MessageInstanceModel.query.filter_by(
                message_type=MessageTypes.send.value,
                status=MessageStatuses.ready.value,
            )
            .filter(cast(Any, MessageInstanceModel.expires_at_in_seconds).isnot(None))
            .filter(cast(Any, MessageInstanceModel.expires_at_in_seconds) <= now)
            .all()
        )
        for message_instance in expired_messages:
            message_instance.status = MessageStatuses.cancelled.value
            db.session.add(message_instance)
        if expired_messages and commit:
            db.session.commit()

    @classmethod
    def correlate_send_message(
        cls,
        message_instance_send: MessageInstanceModel,
        execution_mode: str | None = None,
        receiving_process_instance_id: int | None = None,
        processor_receive: ProcessInstanceProcessor | None = None,
        claim_message_instance: bool = True,
        instrumentation: MessageSendInstrumentation | None = None,
    ) -> MessageInstanceModel | None:
        """Connects the given send message to a 'receive' message if possible.

        :param message_instance_send:
        :return: the message instance that received this message.
        """
        if instrumentation is not None:
            with instrumentation.phase("correlate_expire_ready_send_messages"):
                cls.expire_ready_send_messages()
        else:
            cls.expire_ready_send_messages()

        if claim_message_instance:
            with instrumentation.phase("claim_send_message") if instrumentation is not None else contextlib.nullcontext():
                claimed_send_message = cls._claim_ready_message_instance(message_instance_send)
            if not claimed_send_message:
                return None
        elif message_instance_send.status != MessageStatuses.running.value:
            raise MessageServiceError(
                f"Message instance {message_instance_send.id} must be running when claim_message_instance is False."
            )

        if (
            message_instance_send.expires_at_in_seconds is not None
            and message_instance_send.expires_at_in_seconds <= cls.current_time_in_seconds()
        ):
            cls._transition_message_instance_status(
                message_instance_send,
                MessageStatuses.running.value,
                MessageStatuses.cancelled.value,
            )
            return None

        message_instance_receive: MessageInstanceModel | None = None

        # Let the methods handle the exceptions to ensure the proper variables are set so we do not lose errors

        # First, try to find an existing process instance waiting for this message
        with instrumentation.phase("correlate_existing_receiver") if instrumentation is not None else contextlib.nullcontext():
            message_instance_receive = cls._try_correlate_with_existing_receiver(
                message_instance_send,
                execution_mode,
                receiving_process_instance_id=receiving_process_instance_id,
                processor_receive=processor_receive,
                instrumentation=instrumentation,
            )
        if message_instance_receive is not None:
            if instrumentation is not None:
                instrumentation.set_correlation_result("existing_receive")
            return message_instance_receive

        # No existing receiver found, try to start a new process
        with instrumentation.phase("correlate_message_start") if instrumentation is not None else contextlib.nullcontext():
            message_instance_receive = cls._try_start_new_process_for_message(
                message_instance_send,
                execution_mode,
                instrumentation=instrumentation,
            )
        if message_instance_receive is not None:
            if instrumentation is not None:
                instrumentation.set_correlation_result("message_start")
            return message_instance_receive

        # No match found - reset send message to ready so it can be tried again later
        with instrumentation.phase("reset_unmatched_send_message") if instrumentation is not None else contextlib.nullcontext():
            message_instance_send.status = MessageStatuses.ready.value
            db.session.add(message_instance_send)
            db.session.commit()
        return None

    @classmethod
    def correlate_ready_send_messages_for_process_instance(
        cls,
        message_names: Iterable[str],
        receiving_process_instance: ProcessInstanceModel,
        processor_receive: ProcessInstanceProcessor,
        execution_mode: str | None = None,
    ) -> None:
        cls.expire_ready_send_messages()
        names = list(set(message_names))
        if not names:
            return

        message_instances_send: list[MessageInstanceModel] = (
            MessageInstanceModel.query.filter_by(
                message_type=MessageTypes.send.value,
                status=MessageStatuses.ready.value,
            )
            .filter(MessageInstanceModel.name.in_(names))  # type: ignore
            .filter(cast(Any, MessageInstanceModel.expires_at_in_seconds).isnot(None))
            .order_by(MessageInstanceModel.id)
            .all()
        )

        for message_instance_send in message_instances_send:
            cls.correlate_send_message(
                message_instance_send,
                execution_mode=execution_mode,
                receiving_process_instance_id=receiving_process_instance.id,
                processor_receive=processor_receive,
            )

    @classmethod
    def _try_correlate_with_existing_receiver(
        cls,
        message_instance_send: MessageInstanceModel,
        execution_mode: str | None,
        receiving_process_instance_id: int | None = None,
        processor_receive: ProcessInstanceProcessor | None = None,
        instrumentation: MessageSendInstrumentation | None = None,
    ) -> MessageInstanceModel | None:
        """Try to find and correlate with an existing process instance waiting for this message."""
        available_receive_messages_query = MessageInstanceModel.query.options(
            selectinload(MessageInstanceModel.correlation_rules)
        ).filter_by(
            name=message_instance_send.name,
            status=MessageStatuses.ready.value,
            message_type=MessageTypes.receive.value,
        )
        if receiving_process_instance_id is not None:
            available_receive_messages_query = available_receive_messages_query.filter_by(
                process_instance_id=receiving_process_instance_id
            )
        available_receive_messages: list[MessageInstanceModel] = available_receive_messages_query.all()

        receiving_process_instance: ProcessInstanceModel | None = None
        message_instance_receive: MessageInstanceModel | None = None

        try:
            for message_instance_receive in available_receive_messages:
                if not message_instance_receive.correlates(message_instance_send, CustomBpmnScriptEngine()):
                    continue

                receiving_process_instance = cls.get_process_instance_for_message_instance(message_instance_receive)

                try:
                    with ProcessInstanceQueueService.dequeued(receiving_process_instance, max_attempts=1):
                        if not receiving_process_instance.can_receive_message():
                            continue

                        if not cls._claim_ready_message_instance(message_instance_receive):
                            continue

                        processor_receive_to_use = None
                        if (
                            processor_receive is not None
                            and processor_receive.process_instance_model.id == receiving_process_instance.id
                        ):
                            processor_receive_to_use = processor_receive

                        cls.process_message_receive(
                            receiving_process_instance,
                            message_instance_receive,
                            message_instance_send,
                            execution_mode=execution_mode,
                            processor_receive=processor_receive_to_use,
                            instrumentation=instrumentation,
                        )
                        cls._mark_messages_completed(message_instance_send, message_instance_receive)
                        if processor_receive_to_use is not None:
                            processor_receive_to_use.save()
                        else:
                            db.session.commit()

                        if should_queue_process_instance(execution_mode=execution_mode):
                            queue_process_instance_if_appropriate(receiving_process_instance, execution_mode=execution_mode)

                        return message_instance_receive

                except ProcessInstanceIsAlreadyLockedError:
                    # Someone else has this locked, keep looking for another match
                    continue
        except Exception as exception:
            cls._handle_correlation_failure(
                exception,
                message_instance_send,
                message_instance_receive,
                receiving_process_instance,
            )
            raise

        return None

    @classmethod
    def _claim_ready_message_instance(cls, message_instance: MessageInstanceModel) -> bool:
        """Atomically claim a ready message instance before delivery."""
        return cls._transition_message_instance_status(
            message_instance,
            MessageStatuses.ready.value,
            MessageStatuses.running.value,
        )

    @classmethod
    def _transition_message_instance_status(
        cls,
        message_instance: MessageInstanceModel,
        from_status: str,
        to_status: str,
    ) -> bool:
        rows_updated = (
            db.session.query(MessageInstanceModel)
            .filter(
                MessageInstanceModel.id == message_instance.id,
                MessageInstanceModel.status == from_status,
            )
            .update(
                {
                    "status": to_status,
                    "updated_at_in_seconds": cls.current_time_in_seconds(),
                },
                synchronize_session=False,
            )
        )
        db.session.commit()
        if rows_updated == 0:
            db.session.expire(message_instance)
            return False

        db.session.refresh(message_instance)
        return True

    @classmethod
    def _try_start_new_process_for_message(
        cls,
        message_instance_send: MessageInstanceModel,
        execution_mode: str | None,
        instrumentation: MessageSendInstrumentation | None = None,
    ) -> MessageInstanceModel | None:
        """Try to start a new process instance that can receive this message."""

        receiving_process_instance: ProcessInstanceModel | None = None
        message_instance_receive: MessageInstanceModel | None = None

        try:
            message_triggerable_process_model: MessageTriggerableProcessModel | None = (
                MessageTriggerableProcessModel.query.filter_by(message_name=message_instance_send.name).first()
            )

            if message_triggerable_process_model is None:
                return None

            user: UserModel = (
                message_instance_send.user if message_instance_send.user is not None else UserService.find_or_create_system_user()
            )

            with cls._started_process_with_message(
                message_triggerable_process_model,
                user,
                message_instance_send=message_instance_send,
                execution_mode=execution_mode,
                instrumentation=instrumentation,
            ) as (receiving_process_instance, processor_receive):
                receive_message_phase = (
                    instrumentation.phase("find_started_process_receive_message")
                    if instrumentation is not None
                    else contextlib.nullcontext()
                )
                with receive_message_phase:
                    message_instance_receive = MessageInstanceModel.query.filter_by(
                        process_instance_id=receiving_process_instance.id,
                        message_type=MessageTypes.receive.value,
                        status=MessageStatuses.ready.value,
                    ).first()

                if message_instance_receive is None:
                    raise MessageServiceError(
                        f"Expected to find a receive message instance for newly started process {receiving_process_instance.id}"
                    )

                with instrumentation.phase("claim_receive_message") if instrumentation is not None else contextlib.nullcontext():
                    claimed_receive_message = cls._claim_ready_message_instance(message_instance_receive)
                if not claimed_receive_message:
                    return None

                cls.process_message_receive(
                    receiving_process_instance,
                    message_instance_receive,
                    message_instance_send,
                    execution_mode=execution_mode,
                    processor_receive=processor_receive,
                    instrumentation=instrumentation,
                )
                cls._mark_messages_completed(message_instance_send, message_instance_receive)
                processor_receive.save()

            if should_queue_process_instance(execution_mode=execution_mode):
                queue_process_instance_if_appropriate(receiving_process_instance, execution_mode=execution_mode)

            return message_instance_receive

        except Exception as exception:
            cls._handle_correlation_failure(
                exception,
                message_instance_send,
                message_instance_receive,
                receiving_process_instance,
            )
            raise

    @classmethod
    def _mark_messages_completed(
        cls,
        message_instance_send: MessageInstanceModel,
        message_instance_receive: MessageInstanceModel,
    ) -> None:
        """Mark both send and receive messages as completed and link them."""
        message_instance_receive.status = MessageStatuses.completed.value
        message_instance_receive.counterpart_id = message_instance_send.id
        db.session.add(message_instance_receive)

        message_instance_send.status = MessageStatuses.completed.value
        message_instance_send.counterpart_id = message_instance_receive.id
        db.session.add(message_instance_send)

    @classmethod
    def _handle_correlation_failure(
        cls,
        exception: Exception,
        message_instance_send: MessageInstanceModel,
        message_instance_receive: MessageInstanceModel | None,
        receiving_process_instance: ProcessInstanceModel | None = None,
    ) -> None:
        """Handle failure during message correlation by marking messages as failed."""
        # Don't rollback - the message failed and we need to preserve the failure state
        failure_cause = str(exception)

        message_instance_send.status = MessageStatuses.failed.value
        message_instance_send.failure_cause = failure_cause
        db.session.add(message_instance_send)

        if message_instance_receive is not None:
            message_instance_receive.status = MessageStatuses.failed.value
            message_instance_receive.failure_cause = failure_cause
            db.session.add(message_instance_receive)

        db.session.commit()

        if receiving_process_instance is not None:
            ErrorHandlingService.handle_error(receiving_process_instance, exception)

        if isinstance(exception, SpiffWorkflowException):
            if receiving_process_instance is not None:
                exception.add_note(
                    f"The process instance {receiving_process_instance.id} encountered an error and failed after starting."
                )
            else:
                exception.add_note("The process instance encountered an error and failed after starting.")

    @classmethod
    def _mark_send_message_not_accepted(cls, message_instance_send: MessageInstanceModel, failure_cause: str) -> None:
        message_instance_send.status = MessageStatuses.not_accepted.value
        message_instance_send.failure_cause = failure_cause
        db.session.add(message_instance_send)
        db.session.commit()

    @classmethod
    def _message_not_accepted_message(cls, modified_message_name: str) -> str:
        return (
            "No running process instances correlate with the given message"
            f" name of '{modified_message_name}'.  And this message name is not"
            " currently associated with any process Start Event. Nothing"
            " to do."
        )

    @classmethod
    def _raise_message_not_accepted(cls, message: str) -> NoReturn:
        raise ApiError(
            error_code="message_not_accepted",
            message=message,
            status_code=400,
        )

    @classmethod
    def correlate_all_message_instances(
        cls,
        execution_mode: str | None = None,
    ) -> None:
        """Look at ALL the Send and Receive Messages and attempt to find correlations."""
        cls.expire_ready_send_messages()
        message_instances_send: list[MessageInstanceModel] = MessageInstanceModel.query.filter_by(
            message_type=MessageTypes.send.value,
            status=MessageStatuses.ready.value,
        ).all()

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
        instrumentation: MessageSendInstrumentation | None = None,
    ) -> tuple[ProcessInstanceModel, ProcessInstanceProcessor]:
        """Start up a process instance, so it is ready to catch the event."""
        with cls._started_process_with_message(
            message_triggerable_process_model,
            user,
            message_instance_send=message_instance_send,
            execution_mode=execution_mode,
            instrumentation=instrumentation,
        ) as result:
            return result

    @classmethod
    @contextlib.contextmanager
    def _started_process_with_message(
        cls,
        message_triggerable_process_model: MessageTriggerableProcessModel,
        user: UserModel,
        message_instance_send: MessageInstanceModel | None = None,
        execution_mode: str | None = None,
        instrumentation: MessageSendInstrumentation | None = None,
    ) -> Generator[tuple[ProcessInstanceModel, ProcessInstanceProcessor], None, None]:
        with instrumentation.phase("create_process_instance") if instrumentation is not None else contextlib.nullcontext():
            receiving_process_instance = ProcessInstanceService.create_process_instance_from_process_model_identifier(
                message_triggerable_process_model.process_model_identifier,
                user,
                commit_db=False,
                instrumentation=instrumentation,
            )
            db.session.flush()
        with ProcessInstanceQueueService.dequeued(receiving_process_instance):
            initialize_processor_phase = (
                instrumentation.phase("initialize_process_instance_processor")
                if instrumentation is not None
                else contextlib.nullcontext()
            )
            with initialize_processor_phase:
                processor_receive = ProcessInstanceProcessor(receiving_process_instance)
                cls._cancel_non_matching_start_events(processor_receive, message_triggerable_process_model)

            execution_strategy_name = None
            if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
                execution_strategy_name = "greedy"

            # Add correlations to the BPMN instance if needed so receive messages can use them later.
            if (
                message_instance_send is not None
                and message_instance_send.correlation_keys
                and not processor_receive.bpmn_process_instance.correlations
            ):
                processor_receive.bpmn_process_instance.correlations = message_instance_send.correlation_keys

            # Persist the new receiver before it handles the message. A message-triggered service task can expose a callback
            # URL immediately, and that callback runs in another request.
            with instrumentation.phase("initial_engine_steps") if instrumentation is not None else contextlib.nullcontext():
                processor_receive.do_engine_steps(save=True, execution_strategy_name=execution_strategy_name, needs_dequeue=False)
            yield (receiving_process_instance, processor_receive)

    @staticmethod
    def process_message_receive(
        receiving_process_instance: ProcessInstanceModel,
        message_instance_receive: MessageInstanceModel,
        message_instance_send: MessageInstanceModel,
        execution_mode: str | None = None,
        processor_receive: ProcessInstanceProcessor | None = None,
        instrumentation: MessageSendInstrumentation | None = None,
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
        with instrumentation.phase("calculate_message_correlations") if instrumentation is not None else contextlib.nullcontext():
            correlations = bpmn_message.calculate_correlations(
                CustomBpmnScriptEngine(), bpmn_message.correlation_properties, message_instance_send.payload
            )
        bpmn_event = BpmnEvent(
            event_definition=bpmn_message,
            payload=message_instance_send.payload,
            correlations=correlations,
        )

        processor_receive_to_use: ProcessInstanceProcessor
        save_engine_steps: bool
        if processor_receive is not None:
            processor_receive_to_use = processor_receive
            save_engine_steps = False
        else:
            processor_receive_to_use = ProcessInstanceProcessor(receiving_process_instance)
            save_engine_steps = True

        with instrumentation.phase("send_bpmn_message_event") if instrumentation is not None else contextlib.nullcontext():
            processor_receive_to_use.bpmn_process_instance.send_event(bpmn_event)

        if should_queue_process_instance(execution_mode=execution_mode):
            # even if we are queueing, we ran a "send_event" call up above, and it updated some tasks.
            # we need to serialize these task updates to the db. do_engine_steps with save does that.
            with instrumentation.phase("receive_engine_steps") if instrumentation is not None else contextlib.nullcontext():
                processor_receive_to_use.do_engine_steps(
                    save=save_engine_steps, execution_strategy_name="run_current_ready_tasks", needs_dequeue=save_engine_steps
                )
        elif not ProcessInstanceTmpService.is_enqueued_to_run_in_the_future(receiving_process_instance):
            execution_strategy_name = None
            if execution_mode == ProcessInstanceExecutionMode.synchronous.value:
                execution_strategy_name = "greedy"
            with instrumentation.phase("receive_engine_steps") if instrumentation is not None else contextlib.nullcontext():
                processor_receive_to_use.do_engine_steps(
                    save=save_engine_steps, execution_strategy_name=execution_strategy_name, needs_dequeue=save_engine_steps
                )

        with instrumentation.phase("complete_receive_message") if instrumentation is not None else contextlib.nullcontext():
            message_instance_receive.status = MessageStatuses.completed.value
            db.session.add(message_instance_receive)
            if save_engine_steps:
                db.session.commit()

    @classmethod
    def find_message_triggerable_process_model(cls, modified_message_name: str) -> MessageTriggerableProcessModel:
        message_name, process_group_identifier = MessageInstanceModel.split_modified_message_name(modified_message_name)
        potential_matches: list[MessageTriggerableProcessModel] = MessageTriggerableProcessModel.query.filter_by(
            message_name=message_name
        ).all()
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
        time_to_live_in_seconds: int | None = None,
        message_instance_uuid: str | None = None,
    ) -> MessageInstanceModel:
        message_name, _process_group_identifier = MessageInstanceModel.split_modified_message_name(modified_message_name)
        ttl = cls._validated_time_to_live(time_to_live_in_seconds, message_instance_uuid)
        message_instance_uuid = cls._validated_message_instance_uuid(message_instance_uuid)
        instrumentation = MessageSendInstrumentation(
            modified_message_name=modified_message_name,
            message_name=message_name,
            execution_mode=execution_mode,
            ttl=ttl,
            message_instance_uuid=message_instance_uuid,
        )
        message_instance: MessageInstanceModel | None = None
        now_in_seconds = cls.current_time_in_seconds()
        expires_at_in_seconds = now_in_seconds + ttl if ttl > 0 else None

        try:
            with instrumentation.phase("expire_ready_send_messages"):
                cls.expire_ready_send_messages(now_in_seconds=now_in_seconds)

            with instrumentation.phase("find_existing_message_uuid"):
                existing_message_instance = cls._find_message_with_uuid(
                    message_instance_uuid,
                )

            if existing_message_instance is not None:
                if existing_message_instance.name != message_name or existing_message_instance.payload != body:
                    instrumentation.finish(
                        "message_instance_uuid_conflict",
                        message_instance_id=existing_message_instance.id,
                        error_code="message_instance_uuid_conflict",
                    )
                    raise ApiError(
                        error_code="message_instance_uuid_conflict",
                        message=(
                            "A message with the same message_instance_uuid already exists for a different message or payload."
                        ),
                        status_code=409,
                    )
                if existing_message_instance.status == MessageStatuses.not_accepted.value:
                    instrumentation.finish(
                        "not_accepted",
                        message_instance_id=existing_message_instance.id,
                        error_code="message_not_accepted",
                    )
                    cls._raise_message_not_accepted(
                        existing_message_instance.failure_cause or cls._message_not_accepted_message(modified_message_name)
                    )
                instrumentation.finish("idempotent_replay", message_instance_id=existing_message_instance.id)
                return existing_message_instance

            # Create the send message
            # TODO: support the full message id - including process group - in message instance
            message_instance = MessageInstanceModel(
                message_type=MessageTypes.send.value,
                name=message_name,
                payload=body,
                status=MessageStatuses.running.value,
                user_id=g.user.id,
                message_instance_uuid=message_instance_uuid,
                expires_at_in_seconds=expires_at_in_seconds,
            )
            with instrumentation.phase("create_send_message"):
                db.session.add(message_instance)
                db.session.commit()

            receiver_message = cls.correlate_send_message(
                message_instance,
                execution_mode=execution_mode,
                claim_message_instance=False,
                instrumentation=instrumentation,
            )
            if receiver_message is None:
                if ttl > 0:
                    instrumentation.finish("buffered", message_instance_id=message_instance.id)
                    return message_instance
                message_not_accepted = cls._message_not_accepted_message(modified_message_name)
                with instrumentation.phase("mark_send_message_not_accepted"):
                    cls._mark_send_message_not_accepted(message_instance, message_not_accepted)
                instrumentation.finish(
                    "not_accepted",
                    message_instance_id=message_instance.id,
                    error_code="message_not_accepted",
                )
                cls._raise_message_not_accepted(message_not_accepted)

            instrumentation.finish(
                instrumentation.correlation_result or "correlated",
                message_instance_id=message_instance.id,
                receiver_message_instance_id=receiver_message.id,
                process_instance_id=receiver_message.process_instance_id,
            )
            return receiver_message
        except ApiError as exception:
            if not instrumentation.finished:
                instrumentation.finish(
                    "api_error",
                    message_instance_id=message_instance.id if message_instance is not None else None,
                    error_code=exception.error_code,
                )
            raise
        except Exception as exception:
            if not instrumentation.finished:
                instrumentation.finish(
                    "error",
                    message_instance_id=message_instance.id if message_instance is not None else None,
                    error_code=exception.__class__.__name__,
                )
            raise

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
        receiving_process_instance: ProcessInstanceModel | None = ProcessInstanceModel.query.filter_by(
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

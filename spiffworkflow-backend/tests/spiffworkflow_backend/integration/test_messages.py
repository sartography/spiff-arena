from unittest.mock import patch

import pytest
from flask import Flask
from flask import g
from starlette.testclient import TestClient

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.helpers.spiff_enum import ProcessInstanceExecutionMode
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.routes.messages_controller import message_send
from spiffworkflow_backend.services.data_setup_service import DataSetupService
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestMessages(BaseTest):
    @pytest.mark.parametrize("separate_manual_completions", [False, True])
    @pytest.mark.parametrize("changing_correlation", [False, True])
    def test_parallel_call_activities_reregister_receivers_after_looping(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        separate_manual_completions: bool,
        changing_correlation: bool,
    ) -> None:
        def reply_key(branch: str, iteration: int) -> str:
            return f"{branch}-{iteration}" if changing_correlation else branch

        process_model = load_test_spec(
            "test_group/parallel_message_calls",
            process_model_source_directory="parallel_message_call_activities",
            primary_file_name="main.bpmn",
        )
        with self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", False):
            process_instance = self.create_process_instance_from_process_model(process_model, user=with_super_admin_user)
            g.user = with_super_admin_user
            runtime = ProcessInstanceRuntime(process_instance)
            runtime.do_engine_steps(save=True)
            assert len(runtime.get_ready_user_tasks()) == 2

            if separate_manual_completions:
                for _ in range(2):
                    runtime = ProcessInstanceRuntime(process_instance)
                    self.complete_next_manual_task(
                        runtime,
                        execution_mode=ProcessInstanceExecutionMode.synchronous.value,
                        data={"changing_correlation": changing_correlation},
                    )
            else:
                for task in runtime.get_ready_user_tasks():
                    task.set_data(changing_correlation=changing_correlation)
                    runtime.complete_task(task, with_super_admin_user)
                runtime.do_engine_steps(save=True)

            def assert_waiting(expected_keys: set[str]) -> dict[str, int]:
                # Deserialize from persisted subprocess state, not the runtime that just executed.
                db.session.expire_all()
                reloaded_runtime = ProcessInstanceRuntime(process_instance)
                events = reloaded_runtime.bpmn_process_instance.waiting_events()
                assert {values["reply_key"] for event in events for values in event.correlations.values()} == expected_keys
                receivers = MessageInstanceModel.query.filter_by(
                    process_instance_id=process_instance.id, message_type="receive", status="ready"
                ).all()
                assert len(receivers) == len(expected_keys)
                receiver_ids = {
                    values["reply_key"]: receiver.id for receiver in receivers for values in receiver.correlation_keys.values()
                }
                assert set(receiver_ids) == expected_keys
                return receiver_ids

            favorite_initial = reply_key("favorite", 0)
            other_initial = reply_key("other", 0)
            initial_ids = assert_waiting({favorite_initial, other_initial})

            # A stale subscription must be cancelled even when its message name is still waiting.
            stale_receiver = MessageInstanceModel(
                process_instance_id=process_instance.id,
                message_type="receive",
                name="reply",
                correlation_keys={"MainCorrelationKey": {"reply_key": "stale"}},
            )
            db.session.add(stale_receiver)
            db.session.commit()
            ProcessInstanceRuntime(process_instance).do_engine_steps(save=True)
            assert stale_receiver.status == "cancelled"
            assert assert_waiting({favorite_initial, other_initial}) == initial_ids

            # Finish one subprocess without sending anything to the other. Each loop must
            # register its new correlation and preserve the untouched branch's subscription.
            for branch in ("favorite", "other"):
                for iteration in range(3):
                    response = message_send(
                        "reply",
                        {"reply_key": reply_key(branch, iteration)},
                        ProcessInstanceExecutionMode.synchronous.value,
                    )
                    assert response.status_code == 200
                    expected = {reply_key(branch, iteration + 1)} if iteration < 2 else set()
                    if branch == "favorite":
                        expected.add(other_initial)
                    receiver_ids = assert_waiting(expected)
                    if branch == "favorite":
                        assert receiver_ids[other_initial] == initial_ids[other_initial]

            assert process_instance.status == "complete"
            for message_type in ("send", "receive"):
                assert (
                    MessageInstanceModel.query.filter_by(name="reply", message_type=message_type, status="completed").count() == 6
                )

    def test_asynchronous_message_start_returns_reserved_process_instance(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        load_test_spec(
            "test_group/simple-message-receive",
            process_model_source_directory="simple-message-send-receive",
            bpmn_file_name="message_start_event.bpmn",
        )
        g.user = self.find_or_create_user()

        with (
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True),
            patch("spiffworkflow_backend.services.message_service.queue_message_start_process_instance"),
        ):
            response = message_send(
                "message_one",
                {"payload": "hello"},
                ProcessInstanceExecutionMode.asynchronous.value,
            )

        assert response.status_code == 200
        response_json = response.json
        assert response_json["process_instance"]["id"] is not None
        assert response_json["process_instance"]["status"] == "not_started"
        assert response_json["task_data"] == {}

    def test_get_process_model_for_message(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_model_id = "test_group/message-start-event-with-form"
        process_model = load_test_spec(
            process_model_id=process_model_id,
            process_model_source_directory="message-start-event-with-form",
        )
        response = client.get(
            "/v1.0/messages/bounty_start/process-model",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        response_json = response.json()
        assert response_json["process_model_identifier"] == process_model.id

    def test_message_from_api_into_running_process(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test sending a message to a running process via the API.

        This example workflow will send a message called 'request_approval' and then wait for a response message
        of 'approval_result'.  This test assures that it will fire the message with the correct correlation properties
        and will respond only to a message called 'approval_result' that has the matching correlation properties,
        as sent by an API Call.
        """
        payload = {
            "customer_id": "Sartography",
            "po_number": 1001,
            "description": "We built a new feature for messages!",
            "amount": "100.00",
        }
        process_instance = self.start_sender_process(client, payload, "test_from_api")
        self.assure_a_message_was_sent(process_instance, payload)
        self.assure_there_is_a_process_waiting_on_a_message(process_instance)
        g.user = process_instance.process_initiator

        # Make an API call to the service endpoint, but use the wrong po number
        with pytest.raises(ApiError):
            message_send("Approval Result", {"payload": {"po_number": 5001}})

        # Should return an error when making an API call for right po number, wrong client
        with pytest.raises(ApiError):
            message_send(
                "Approval Result",
                {"po_number": 1001, "customer_id": "jon"},
            )

        # No error when calling with the correct parameters
        response = message_send(
            "Approval Result",
            {"po_number": 1001, "customer_id": "Sartography"},
        )

        # The response's task data should also match up with the correlation keys.
        assert response.json["task_data"]["po_number"] == 1001
        assert response.json["task_data"]["customer_id"] == "Sartography"

        # There is no longer a waiting message
        waiting_messages = (
            MessageInstanceModel.query.filter_by(message_type="receive")
            .filter_by(status="ready")
            .filter_by(process_instance_id=process_instance.id)
            .all()
        )
        assert len(waiting_messages) == 0
        # The process has completed
        assert process_instance.status == "complete"

    def test_message_model_list_up_search(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.refresh_process_model_caches()
        response = client.get(
            "/v1.0/message-models/examples:1-basic-concepts",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
        )
        assert response.status_code == 200
        assert response.json() is not None
        assert len(response.json()["messages"]) == 4

        response = client.get(
            "/v1.0/message-models",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
        )
        assert response.status_code == 200
        assert response.json() is not None
        assert len(response.json()["messages"]) == 0, "should not have access to messages defined in a sub directory"

    def test_message_model_list_all(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.copy_example_process_models()
        DataSetupService.refresh_process_model_caches()
        response = client.get(
            "/v1.0/all-message-models",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
        )
        assert response.status_code == 200
        assert response.json() is not None
        assert len(response.json()["messages"]) == 4

    def test_creating_shared_message_immediately_lists_existing_bpmn_usage(
        self, app: Flask, client: TestClient, with_db_and_bpmn_file_cleanup: None, with_super_admin_user: UserModel
    ) -> None:
        self.create_process_group("test_group")
        load_test_spec(
            "test_group/receiver",
            process_model_source_directory="simple-message-send-receive",
            bpmn_file_name="message_start_event.bpmn",
        )
        models = ProcessModelService.get_process_models(process_group_id="test_group", recursive=True)
        assert models
        references = SpecFileService.get_references_for_process(models[0])
        message_identifier = "Message_0rcwl5q"
        assert message_identifier in {name for ref in references for name in ref.messages}
        assert MessageModel.query.filter_by(identifier=message_identifier).count() == 0
        headers = self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"})
        # Check both initial creation and a repeated save: usage must remain present without duplicates.
        for _ in range(2):
            response = client.put(
                "/v1.0/process-groups/test_group",
                headers=headers,
                json={"display_name": "Test Group", "messages": {message_identifier: {"schema": {}}}},
            )
            assert response.status_code == 200
            response = client.get("/v1.0/message-models/test_group", headers=headers)
            assert response.status_code == 200
            message = next(message for message in response.json()["messages"] if message["identifier"] == message_identifier)
            assert message["process_model_identifiers"] == ["test_group/receiver"]

    def test_process_group_update_syncs_message_models(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group("bob")

        response = client.get(
            "/v1.0/message-models/bob",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
        )
        assert response.status_code == 200
        assert response.json() is not None
        assert len(response.json()["messages"]) == 0

        process_group = {
            "admin": False,
            "description": "Bob's Group",
            "display_name": "Bob",
            "display_order": 40,
            "parent_groups": None,
            "messages": {
                "table_seated": {
                    "correlation_properties": {
                        "table_number": {
                            "retrieval_expression": "table_number",
                        },
                        "franchise_id": {
                            "retrieval_expression": "franchise_id",
                        },
                    },
                    "schema": {},
                },
                "order_ready": {
                    "correlation_properties": {
                        "table_number": {
                            "retrieval_expression": "table_number",
                        },
                        "franchise_id": {
                            "retrieval_expression": "franchise_id",
                        },
                    },
                    "schema": {},
                },
                "end_of_day_receipts": {
                    "schema": {},
                },
            },
        }

        response = client.put(
            "/v1.0/process-groups/bob",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
            json=process_group,
        )
        assert response.status_code == 200

        response = client.get(
            "/v1.0/message-models/bob",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
        )
        assert response.status_code == 200
        assert response.json() is not None
        assert "messages" in response.json()

        messages = response.json()["messages"]
        expected_message_identifiers = {"table_seated", "order_ready", "end_of_day_receipts"}
        assert len(messages) == len(expected_message_identifiers)

        expected_correlation_properties = {
            "table_seated": {"table_number": "table_number", "franchise_id": "franchise_id"},
            "order_ready": {"table_number": "table_number", "franchise_id": "franchise_id"},
            "end_of_day_receipts": {},
        }

        for message in messages:
            assert isinstance(message["id"], int)
            assert message["identifier"] in expected_message_identifiers
            assert message["location"] == "bob"
            assert message["schema"] == {}

            cp = {p["identifier"]: p["retrieval_expression"] for p in message["correlation_properties"]}
            assert cp == expected_correlation_properties[message["identifier"]]

    def test_process_group_update_rejects_existing_message_id_at_different_location(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group("order")
        self.create_process_group("order/request-for-information")

        process_group = {
            "display_name": "Order",
            "messages": {
                "request-for-information-received": {
                    "schema": {},
                }
            },
        }
        response = client.put(
            "/v1.0/process-groups/order",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
            json=process_group,
        )
        assert response.status_code == 200

        original_message = MessageModel.query.filter_by(
            identifier="request-for-information-received",
            location="order",
        ).one()
        original_message_id = original_message.id

        response = client.put(
            "/v1.0/process-groups/order:request-for-information",
            headers=self.logged_in_headers(with_super_admin_user, additional_headers={"Content-Type": "application/json"}),
            json={
                "display_name": "Request For Information",
                "messages": {
                    "request-for-information-received": {
                        "id": original_message_id,
                        "location": "order/request-for-information",
                        "schema": {},
                    }
                },
            },
        )
        assert response.status_code == 400

        original_message = MessageModel.query.filter_by(id=original_message_id).one()
        assert original_message.identifier == "request-for-information-received"
        assert original_message.location == "order"

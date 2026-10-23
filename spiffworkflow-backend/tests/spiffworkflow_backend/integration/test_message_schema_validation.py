import uuid
from typing import Any
from unittest.mock import patch

import pytest
from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.message_service import MessageService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest

AMOUNT_SCHEMA = {
    "type": "object",
    "properties": {"amount": {"type": "integer"}},
    "required": ["amount"],
    "additionalProperties": False,
}
VALIDATE_MESSAGES = "SPIFFWORKFLOW_BACKEND_VALIDATE_MESSAGE_BODY_AGAINST_SCHEMA"


class TestMessageSchemaValidation(BaseTest):
    """Validate against the selected recipient, not the request's optional group prefix."""

    def _set_schema(self, client: TestClient, user: UserModel, group: str, name: str, schema: Any) -> None:
        response = client.put(
            f"/v1.0/process-groups/{group.replace('/', ':')}",
            headers=self.logged_in_headers(user),
            json={"display_name": group, "messages": {name: {"schema": schema}}},
        )
        assert response.status_code == 200, response.json()

    def _create_message_start(self, client: TestClient, user: UserModel, group: str = "test_group") -> None:
        self.create_group_and_model_with_bpmn(
            client,
            user,
            process_group_id=group,
            process_model_id="simple-message-receive",
            bpmn_file_location="simple-message-send-receive",
            bpmn_file_name="message_start_event.bpmn",
        )

    @pytest.mark.parametrize("name", ["message_one", "test_group:message_one", "unrelated:message_one"])
    @pytest.mark.parametrize("payload", [{}, {"amount": "100"}, {"amount": 100, "extra": True}])
    def test_validation_before_message_start(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        name: str,
        payload: dict,
    ) -> None:
        self._create_message_start(client, with_super_admin_user)
        self._set_schema(client, with_super_admin_user, "test_group", "message_one", AMOUNT_SCHEMA)
        headers = self.logged_in_headers(with_super_admin_user)
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            response = client.post(f"/v1.0/messages/{name}", headers=headers, json=payload)
            assert response.status_code == 400
            assert response.json()["error_code"] == "message_data_validation_error"
            assert "test_group" in response.json()["message"]
            rejected = MessageInstanceModel.query.one()
            assert rejected.status == "not_accepted"
            assert rejected.failure_cause == response.json()["message"]
            assert ProcessInstanceModel.query.count() == 0

            response = client.post(f"/v1.0/messages/{name}", headers=headers, json={"amount": 100})
            assert response.status_code == 200, response.json()
            assert response.json()["task_data"]["the_message"] == {"amount": 100}
            assert response.json()["process_instance"]["status"] == "complete"

    @pytest.mark.parametrize("enabled", [True, False])
    def test_async_start_validation_precedes_reservation_and_enqueue(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        enabled: bool,
    ) -> None:
        self._create_message_start(client, with_super_admin_user)
        self._set_schema(client, with_super_admin_user, "test_group", "message_one", AMOUNT_SCHEMA)
        with (
            self.app_config_mock(app, VALIDATE_MESSAGES, enabled),
            self.app_config_mock(app, "SPIFFWORKFLOW_BACKEND_CELERY_ENABLED", True),
            patch("spiffworkflow_backend.services.message_service.queue_message_start_process_instance") as enqueue,
        ):
            response = client.post(
                "/v1.0/messages/message_one?execution_mode=asynchronous",
                headers=self.logged_in_headers(with_super_admin_user),
                json={},
            )
        if enabled:
            assert response.status_code == 400
            assert response.json()["error_code"] == "message_data_validation_error"
            assert ProcessInstanceModel.query.count() == 0
            enqueue.assert_not_called()
        else:
            assert response.status_code == 200, response.json()
            assert response.json()["process_instance"]["status"] == "not_started"
            enqueue.assert_called_once()

    @pytest.mark.parametrize("child_schema", [AMOUNT_SCHEMA, {}, None])
    def test_nearest_receiver_definition_shadows_parent_and_ignores_other_groups(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        child_schema: Any,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group")
        self._set_schema(client, with_super_admin_user, "test_group", "message_one", False)
        self._create_message_start(client, with_super_admin_user, "test_group/child")
        self._set_schema(client, with_super_admin_user, "test_group/child", "message_one", child_schema)
        self.create_process_group_with_api(client, with_super_admin_user, "unrelated")
        self._set_schema(client, with_super_admin_user, "unrelated", "message_one", False)
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            response = client.post(
                "/v1.0/messages/unrelated:message_one",
                headers=self.logged_in_headers(with_super_admin_user),
                json={"amount": 100},
            )
        assert response.status_code == 200, response.json()

    def test_receiver_inherits_parent_definition(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group")
        self._set_schema(client, with_super_admin_user, "test_group", "message_one", AMOUNT_SCHEMA)
        self._create_message_start(client, with_super_admin_user, "test_group/child")
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            response = client.post(
                "/v1.0/messages/message_one",
                headers=self.logged_in_headers(with_super_admin_user),
                json={},
            )
        assert response.status_code == 400
        assert response.json()["error_code"] == "message_data_validation_error"
        assert ProcessInstanceModel.query.count() == 0

    @pytest.mark.parametrize("schema", ["missing", None, {}, "", "{}", True, "true"])
    def test_missing_and_permissive_schemas(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        schema: Any,
    ) -> None:
        self._create_message_start(client, with_super_admin_user)
        if schema != "missing":
            self._set_schema(client, with_super_admin_user, "test_group", "message_one", schema)
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            response = client.post(
                "/v1.0/messages/message_one",
                headers=self.logged_in_headers(with_super_admin_user),
                json={"anything": True},
            )
        assert response.status_code == 200, response.json()

    @pytest.mark.parametrize(
        "schema", [False, "false", "{broken json", {"type": "invalid"}, "null", "0", "[]", " ", {"$ref": "#/$defs/missing"}]
    )
    def test_false_or_invalid_schema_rejects_before_start_even_with_ttl(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        schema: Any,
    ) -> None:
        self._create_message_start(client, with_super_admin_user)
        self._set_schema(client, with_super_admin_user, "test_group", "message_one", schema)
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            response = client.post(
                f"/v1.0/messages/message_one?time_to_live_in_seconds=60&message_instance_uuid={uuid.uuid4()}",
                headers=self.logged_in_headers(with_super_admin_user),
                json={},
            )
        assert response.status_code == 400
        assert response.json()["error_code"] == "message_data_validation_error"
        assert MessageInstanceModel.query.one().status == "not_accepted"
        assert ProcessInstanceModel.query.count() == 0

    def test_replay_is_validated_against_known_recipient_current_schema(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self._create_message_start(client, with_super_admin_user)
        self._set_schema(client, with_super_admin_user, "test_group", "message_one", {})
        url = f"/v1.0/messages/message_one?message_instance_uuid={uuid.uuid4()}"
        headers = self.logged_in_headers(with_super_admin_user)
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            assert client.post(url, headers=headers, json={}).status_code == 200
            assert client.post(url, headers=headers, json={}).status_code == 200
            self._set_schema(client, with_super_admin_user, "test_group", "message_one", AMOUNT_SCHEMA)
            response = client.post(url, headers=headers, json={})
            assert response.status_code == 400
            assert response.json()["error_code"] == "message_data_validation_error"
        assert ProcessInstanceModel.query.count() == 1
        assert {message.status for message in MessageInstanceModel.query.all()} == {"completed"}

    @pytest.mark.parametrize("buffered", [True, False])
    @pytest.mark.parametrize("enabled", [True, False])
    def test_invalid_message_does_not_consume_waiting_receiver_or_fail_process(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
        buffered: bool,
        enabled: bool,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group")
        self._set_schema(client, with_super_admin_user, "test_group", "Approval Result", {"required": ["amount"]})
        payload = {"customer_id": "Sartography", "po_number": 1001}
        headers = self.logged_in_headers(with_super_admin_user)
        key = str(uuid.uuid4())
        url = f"/v1.0/messages/Approval Result?time_to_live_in_seconds=60&message_instance_uuid={key}"
        with self.app_config_mock(app, VALIDATE_MESSAGES, enabled):
            if buffered:
                response = client.post(url, headers=headers, json=payload)
                assert response.status_code == 202, response.json()
                assert MessageInstanceModel.query.filter_by(message_instance_uuid=key).one().status == "ready"
                assert client.post(url, headers=headers, json=payload).status_code == 202

            process_instance = self.start_sender_process(client, {**payload, "amount": 100, "description": "Test order"})
            if buffered:
                # Exercises background correlation as well as the opportunistic delivery done
                # when a receiver first becomes available. Rejection must not propagate an error.
                MessageService.correlate_all_message_instances()
            else:
                response = client.post(url, headers=headers, json=payload)
                assert response.status_code == (400 if enabled else 200), response.json()
                if enabled:
                    assert response.json()["error_code"] == "message_data_validation_error"

            db.session.refresh(process_instance)
            message = MessageInstanceModel.query.filter_by(message_instance_uuid=key).one()
            if enabled:
                assert message.status == "not_accepted"
                assert "amount" in message.failure_cause
                assert process_instance.status != "error"
                self.assure_there_is_a_process_waiting_on_a_message(process_instance)
                replay = client.post(url, headers=headers, json=payload)
                assert replay.status_code == 400
                assert replay.json()["error_code"] == "message_not_accepted"
                assert "amount" in replay.json()["message"]
                response = client.post("/v1.0/messages/Approval Result", headers=headers, json={**payload, "amount": 100})
                assert response.status_code == 200, response.json()
            else:
                assert message.status == "completed"
            db.session.refresh(process_instance)
            assert process_instance.status == "complete"

    def test_buffered_rejection_does_not_block_a_later_valid_send(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group")
        self._set_schema(client, with_super_admin_user, "test_group", "Approval Result", {"required": ["amount"]})
        payload = {"customer_id": "Sartography", "po_number": 1001}
        keys = [str(uuid.uuid4()), str(uuid.uuid4())]
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            for key, body in zip(keys, [payload, {**payload, "amount": 100}], strict=True):
                response = client.post(
                    f"/v1.0/messages/Approval Result?time_to_live_in_seconds=60&message_instance_uuid={key}",
                    headers=self.logged_in_headers(with_super_admin_user),
                    json=body,
                )
                assert response.status_code == 202
            process_instance = self.start_sender_process(client, {**payload, "amount": 100, "description": "Test order"})
            MessageService.correlate_all_message_instances()
            assert MessageInstanceModel.query.filter_by(message_instance_uuid=keys[0]).one().status == "not_accepted"
            assert MessageInstanceModel.query.filter_by(message_instance_uuid=keys[1]).one().status == "completed"
            db.session.refresh(process_instance)
            assert process_instance.status == "complete"

    def test_internal_message_validation_is_unchanged(self, app: Flask) -> None:
        message = MessageInstanceModel(process_instance_id=123, name="internal", message_type="send", payload={})
        with (
            self.app_config_mock(app, VALIDATE_MESSAGES, True),
            patch.object(MessageService, "validate_message_body") as validate,
        ):
            assert MessageService._validate_external_message_for_receiver(message, "test_group/model")
        validate.assert_not_called()

    def test_buffered_message_uses_schema_current_when_receiver_appears(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group")
        self._set_schema(client, with_super_admin_user, "test_group", "Approval Result", {})
        payload = {"customer_id": "Sartography", "po_number": 1001}
        key = str(uuid.uuid4())
        with self.app_config_mock(app, VALIDATE_MESSAGES, True):
            response = client.post(
                f"/v1.0/messages/Approval Result?time_to_live_in_seconds=60&message_instance_uuid={key}",
                headers=self.logged_in_headers(with_super_admin_user),
                json=payload,
            )
            assert response.status_code == 202
            self._set_schema(client, with_super_admin_user, "test_group", "Approval Result", False)
            process_instance = self.start_sender_process(client, {**payload, "amount": 100, "description": "Test order"})
            MessageService.correlate_all_message_instances()
            assert MessageInstanceModel.query.filter_by(message_instance_uuid=key).one().status == "not_accepted"
            self.assure_there_is_a_process_waiting_on_a_message(process_instance)
            assert process_instance.status != "error"

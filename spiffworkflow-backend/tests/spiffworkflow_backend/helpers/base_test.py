import copy
import datetime
import io
import json
import os
import shutil
import time
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from flask import current_app
from flask.app import Flask
from flask.testing import FlaskClient
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.message_instance import MessageInstanceModel
from spiffworkflow_backend.models.permission_assignment import Permission
from spiffworkflow_backend.models.permission_target import PermissionTargetModel
from spiffworkflow_backend.models.principal import PrincipalModel
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_group import ProcessGroupSchema
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_instance_report import FilterValue
from spiffworkflow_backend.models.process_instance_report import ProcessInstanceReportModel
from spiffworkflow_backend.models.process_instance_report import ReportMetadata
from spiffworkflow_backend.models.process_model import NotificationType
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.process_model import ProcessModelInfoSchema
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_queue_service import ProcessInstanceQueueService
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.user_service import UserService
from sqlalchemy.orm.attributes import flag_modified
from werkzeug.test import TestResponse  # type: ignore

from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

# from tests.spiffworkflow_backend.helpers.test_data import logged_in_headers


class BaseTest:
    @staticmethod
    def find_or_create_user(username: str = "test_user_1") -> UserModel:
        user = UserModel.query.filter_by(username=username).first()
        if isinstance(user, UserModel):
            return user

        user = UserService.create_user(username, "internal", username)
        if isinstance(user, UserModel):
            return user

        raise ApiError(
            error_code="create_user_error",
            message=f"Cannot find or create user: {username}",
        )

    @staticmethod
    def logged_in_headers(user: UserModel, extra_token_payload: dict | None = None) -> dict[str, str]:
        return {"Authorization": "Bearer " + user.encode_auth_token(extra_token_payload)}

    def create_group_and_model_with_bpmn(
        self,
        client: FlaskClient,
        user: UserModel,
        process_group_id: str | None = "test_group",
        process_model_id: str | None = "random_fact",
        bpmn_file_name: str | None = None,
        bpmn_file_location: str | None = None,
    ) -> ProcessModelInfo:
        """Creates a process group.

        Creates a process model
        Adds a bpmn file to the model.
        """
        process_group_display_name = process_group_id or ""
        process_group_description = process_group_id or ""
        process_model_identifier = f"{process_group_id}/{process_model_id}"
        if bpmn_file_location is None:
            bpmn_file_location = process_model_id

        self.create_process_group_with_api(client, user, process_group_description, process_group_display_name)

        self.create_process_model_with_api(
            client,
            process_model_id=process_model_identifier,
            process_model_display_name=process_group_display_name,
            process_model_description=process_group_description,
            user=user,
        )

        process_model = load_test_spec(
            process_model_id=process_model_identifier,
            bpmn_file_name=bpmn_file_name,
            process_model_source_directory=bpmn_file_location,
        )

        return process_model

    def create_and_run_process_instance(
        self,
        client: FlaskClient,
        user: UserModel,
        process_group_id: str | None = "test_group",
        process_model_id: str | None = "random_fact",
        bpmn_file_name: str | None = None,
        bpmn_file_location: str | None = None,
    ) -> tuple[ProcessModelInfo, int]:
        process_model = self.create_group_and_model_with_bpmn(
            client=client,
            user=user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_name=bpmn_file_name,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.json is not None
        process_instance_id = response.json["id"]
        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=self.logged_in_headers(user),
        )

        assert response.status_code == 200
        assert response.json is not None

        return (process_model, int(process_instance_id))

    def create_process_group(
        self,
        process_group_id: str,
        display_name: str = "",
    ) -> ProcessGroup:
        process_group_parent_id = "/".join(process_group_id.rsplit("/", 1)[:-1])
        if process_group_parent_id != "":
            if not ProcessModelService.is_process_group_identifier(process_group_parent_id):
                raise Exception(
                    f"Parent process group does not exist for '{process_group_id}'. Parent was '{process_group_parent_id}'"
                )
        process_group = ProcessGroup(id=process_group_id, display_name=display_name, display_order=0, admin=False)
        return ProcessModelService.add_process_group(process_group)

    def create_process_group_with_api(
        self,
        client: FlaskClient,
        user: Any,
        process_group_id: str,
        display_name: str = "",
    ) -> str:
        process_group = ProcessGroup(id=process_group_id, display_name=display_name, display_order=0, admin=False)
        response = client.post(
            "/v1.0/process-groups",
            headers=self.logged_in_headers(user),
            content_type="application/json",
            data=json.dumps(ProcessGroupSchema().dump(process_group)),
        )
        assert response.status_code == 201
        assert response.json is not None
        assert response.json["id"] == process_group_id
        return process_group_id

    def create_process_model(
        self,
        process_model_id: str,
        display_name: str | None = None,
    ) -> ProcessModelInfo:
        process_group_parent_id = "/".join(process_model_id.rsplit("/", 1)[:-1])
        if process_group_parent_id != "":
            if not ProcessModelService.is_process_group_identifier(process_group_parent_id):
                raise Exception(
                    f"Parent process group does not exist for '{process_model_id}'. Parent was '{process_group_parent_id}'"
                )
        process_model = ProcessModelInfo(id=process_model_id, display_name=process_model_id, description=process_model_id)
        ProcessModelService.save_process_model(process_model)
        return process_model

    def create_process_model_with_api(
        self,
        client: FlaskClient,
        process_model_id: str | None = None,
        process_model_display_name: str = "Cooooookies",
        process_model_description: str = "Om nom nom delicious cookies",
        fault_or_suspend_on_exception: str = NotificationType.suspend.value,
        exception_notification_addresses: list | None = None,
        primary_process_id: str | None = None,
        primary_file_name: str | None = None,
        user: UserModel | None = None,
    ) -> TestResponse:
        if process_model_id is not None:
            # make sure we have a group
            process_group_id, _ = os.path.split(process_model_id)
            modified_process_group_id = process_group_id.replace("/", ":")
            process_group_path = os.path.abspath(os.path.join(FileSystemService.root_path(), process_group_id))
            if ProcessModelService.is_process_group(process_group_path):
                if exception_notification_addresses is None:
                    exception_notification_addresses = []

                model = ProcessModelInfo(
                    id=process_model_id,
                    display_name=process_model_display_name,
                    description=process_model_description,
                    primary_process_id=primary_process_id,
                    primary_file_name=primary_file_name,
                    fault_or_suspend_on_exception=fault_or_suspend_on_exception,
                    exception_notification_addresses=exception_notification_addresses,
                )
                if user is None:
                    user = self.find_or_create_user()

                response = client.post(
                    f"/v1.0/process-models/{modified_process_group_id}",
                    content_type="application/json",
                    data=json.dumps(ProcessModelInfoSchema().dump(model)),
                    headers=self.logged_in_headers(user),
                )

                assert response.status_code == 201
                return response

            else:
                raise Exception("You must create the group first")
        else:
            raise Exception("You must include the process_model_id, which must be a path to the model")

    def get_test_data_file_full_path(self, file_name: str, process_model_test_data_dir: str) -> str:
        return os.path.join(
            current_app.instance_path,
            "..",
            "..",
            "tests",
            "data",
            process_model_test_data_dir,
            file_name,
        )

    def get_test_data_file_contents(self, file_name: str, process_model_test_data_dir: str) -> bytes:
        file_full_path = self.get_test_data_file_full_path(file_name, process_model_test_data_dir)
        with open(file_full_path, "rb") as file:
            return file.read()

    def create_spec_file(
        self,
        client: FlaskClient,
        process_model_id: str,
        process_model_location: str | None = None,
        process_model: ProcessModelInfo | None = None,
        file_name: str = "random_fact.bpmn",
        file_data: bytes = b"abcdef",
        user: UserModel | None = None,
    ) -> Any:
        """Test_create_spec_file.

        Adds a bpmn file to the model.
        process_model_id is the destination path
        process_model_location is the source path

        because of permissions, user might be required now..., not sure yet.
        """
        if process_model_location is None:
            process_model_location = file_name.split(".")[0]
        if process_model is None:
            process_model = load_test_spec(
                process_model_id=process_model_id,
                bpmn_file_name=file_name,
                process_model_source_directory=process_model_location,
            )
        data = {"file": (io.BytesIO(file_data), file_name)}
        if user is None:
            user = self.find_or_create_user()
        modified_process_model_id = process_model.id.replace("/", ":")
        response = client.post(
            f"/v1.0/process-models/{modified_process_model_id}/files",
            data=data,
            follow_redirects=True,
            content_type="multipart/form-data",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 201
        assert response.get_data() is not None
        file = json.loads(response.get_data(as_text=True))
        # assert FileType.svg.value == file["type"]
        # assert "image/svg+xml" == file["content_type"]

        response = client.get(
            f"/v1.0/process-models/{modified_process_model_id}/files/{file_name}",
            headers=self.logged_in_headers(user),
        )
        assert response.status_code == 200
        file2 = json.loads(response.get_data(as_text=True))
        assert file["file_contents"] == file2["file_contents"]
        return file

    @staticmethod
    def create_process_instance_from_process_model_id_with_api(
        client: FlaskClient,
        test_process_model_id: str,
        headers: dict[str, str],
    ) -> TestResponse:
        """Create_process_instance.

        There must be an existing process model to instantiate.
        """
        if not ProcessModelService.is_process_model_identifier(test_process_model_id):
            dirname = os.path.dirname(test_process_model_id)
            if not ProcessModelService.is_process_group_identifier(dirname):
                process_group = ProcessGroup(id=dirname, display_name=dirname)
                ProcessModelService.add_process_group(process_group)
            basename = os.path.basename(test_process_model_id)
            load_test_spec(
                process_model_id=test_process_model_id,
                process_model_source_directory=basename,
                bpmn_file_name=basename,
            )
        modified_process_model_id = test_process_model_id.replace("/", ":")
        response = client.post(
            f"/v1.0/process-instances/{modified_process_model_id}",
            headers=headers,
        )
        assert response.status_code == 201
        return response

    # @staticmethod
    # def get_public_access_token(username: str, password: str) -> dict:
    #     """Get_public_access_token."""
    #     public_access_token = AuthenticationService().get_public_access_token(
    #         username, password
    #     )
    #     return public_access_token

    def create_process_instance_from_process_model(
        self,
        process_model: ProcessModelInfo,
        status: str | None = "not_started",
        user: UserModel | None = None,
        save_start_and_end_times: bool = True,
        bpmn_version_control_identifier: str | None = None,
    ) -> ProcessInstanceModel:
        if user is None:
            user = self.find_or_create_user()

        current_time = round(time.time())
        start_in_seconds = None
        end_in_seconds = None
        if save_start_and_end_times:
            start_in_seconds = current_time - (3600 * 1)
            end_in_seconds = current_time - (3600 * 1 - 20)
        process_instance = ProcessInstanceModel(
            status=status,
            process_initiator=user,
            process_model_identifier=process_model.id,
            process_model_display_name=process_model.display_name,
            updated_at_in_seconds=round(time.time()),
            start_in_seconds=start_in_seconds,
            end_in_seconds=end_in_seconds,
            bpmn_version_control_identifier=bpmn_version_control_identifier,
        )
        db.session.add(process_instance)
        db.session.commit()

        run_at_in_seconds = round(time.time())
        ProcessInstanceQueueService.enqueue_new_process_instance(process_instance, run_at_in_seconds)

        return process_instance

    @classmethod
    def create_user_with_permission(
        cls,
        username: str,
        target_uri: str = PermissionTargetModel.URI_ALL,
        permission_names: list[str] | None = None,
        grant_type: str = "permit",
    ) -> UserModel:
        user = BaseTest.find_or_create_user(username=username)
        return cls.add_permissions_to_user(user, target_uri=target_uri, permission_names=permission_names, grant_type=grant_type)

    @classmethod
    def add_permissions_to_user(
        cls,
        user: UserModel,
        target_uri: str = PermissionTargetModel.URI_ALL,
        permission_names: list[str] | None = None,
        grant_type: str = "permit",
    ) -> UserModel:
        principal = user.principal
        cls.add_permissions_to_principal(
            principal, target_uri=target_uri, permission_names=permission_names, grant_type=grant_type
        )
        return user

    @classmethod
    def add_permissions_to_principal(
        cls, principal: PrincipalModel, target_uri: str, permission_names: list[str] | None, grant_type: str = "permit"
    ) -> None:
        permission_target = AuthorizationService.find_or_create_permission_target(target_uri)

        if permission_names is None:
            permission_names = [member.name for member in Permission]

        for permission in permission_names:
            AuthorizationService.create_permission_for_principal(
                principal=principal,
                permission_target=permission_target,
                permission=permission,
                grant_type=grant_type,
            )

    def assert_user_has_permission(
        self,
        user: UserModel,
        permission: str,
        target_uri: str,
        expected_result: bool = True,
    ) -> None:
        has_permission = AuthorizationService.user_has_permission(
            user=user,
            permission=permission,
            target_uri=target_uri,
        )
        assert has_permission is expected_result

    def modify_process_identifier_for_path_param(self, identifier: str) -> str:
        return ProcessModelInfo.modify_process_identifier_for_path_param(identifier)

    def un_modify_modified_process_identifier_for_path_param(self, modified_identifier: str) -> str:
        return modified_identifier.replace(":", "/")

    def create_process_model_with_metadata(self) -> ProcessModelInfo:
        self.create_process_group("test_group", "test_group")
        process_model = load_test_spec(
            "test_group/hello_world",
            process_model_source_directory="nested-task-data-structure",
        )
        ProcessModelService.update_process_model(
            process_model,
            {
                "metadata_extraction_paths": [
                    {"key": "awesome_var", "path": "outer.inner"},
                    {"key": "invoice_number", "path": "invoice_number"},
                ]
            },
        )
        return process_model

    def post_to_process_instance_list(
        self,
        client: FlaskClient,
        user: UserModel,
        report_metadata: ReportMetadata | None = None,
        param_string: str | None = "",
    ) -> TestResponse:
        report_metadata_to_use = report_metadata
        if report_metadata_to_use is None:
            report_metadata_to_use = self.empty_report_metadata_body()
        response = client.post(
            f"/v1.0/process-instances{param_string}",
            headers=self.logged_in_headers(user),
            content_type="application/json",
            data=json.dumps({"report_metadata": report_metadata_to_use}),
        )
        assert response.status_code == 200
        assert response.json is not None
        return response

    def empty_report_metadata_body(self) -> ReportMetadata:
        return {"filter_by": [], "columns": [], "order_by": []}

    def start_sender_process(
        self,
        client: FlaskClient,
        payload: dict,
        group_name: str = "test_group",
    ) -> ProcessInstanceModel:
        process_model = load_test_spec(
            "test_group/message",
            process_model_source_directory="message_send_one_conversation",
            bpmn_file_name="message_sender.bpmn",  # Slightly misnamed, it sends and receives
        )

        process_instance = self.create_process_instance_from_process_model(process_model)
        processor_send_receive = ProcessInstanceProcessor(process_instance)
        processor_send_receive.do_engine_steps(save=True)
        task = processor_send_receive.get_all_user_tasks()[0]
        human_task = process_instance.active_human_tasks[0]

        ProcessInstanceService.complete_form_task(
            processor_send_receive,
            task,
            payload,
            process_instance.process_initiator,
            human_task,
        )
        processor_send_receive.save()
        return process_instance

    def assure_a_message_was_sent(self, process_instance: ProcessInstanceModel, payload: dict) -> None:
        # There should be one new send message for the given process instance.
        send_messages = (
            MessageInstanceModel.query.filter_by(message_type="send")
            .filter_by(process_instance_id=process_instance.id)
            .order_by(MessageInstanceModel.id)
            .all()
        )
        assert len(send_messages) == 1
        send_message = send_messages[0]
        assert send_message.payload == payload, "The send message should match up with the payload"
        assert send_message.name == "Request Approval"
        assert send_message.status == "ready"

    def assure_there_is_a_process_waiting_on_a_message(self, process_instance: ProcessInstanceModel) -> None:
        # There should be one new send message for the given process instance.
        waiting_messages = (
            MessageInstanceModel.query.filter_by(message_type="receive")
            .filter_by(status="ready")
            .filter_by(process_instance_id=process_instance.id)
            .order_by(MessageInstanceModel.id)
            .all()
        )
        assert len(waiting_messages) == 1
        waiting_message = waiting_messages[0]
        self.assure_correlation_properties_are_right(waiting_message)

    def assure_correlation_properties_are_right(self, message: MessageInstanceModel) -> None:
        # Correlation Properties should match up
        po_curr = next(c for c in message.correlation_rules if c.name == "po_number")
        customer_curr = next(c for c in message.correlation_rules if c.name == "customer_id")
        assert po_curr is not None
        assert customer_curr is not None

    def create_process_instance_with_synthetic_metadata(
        self, process_model: ProcessModelInfo, process_instance_metadata_dict: dict
    ) -> ProcessInstanceModel:
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        for key, value in process_instance_metadata_dict.items():
            process_instance_metadata = ProcessInstanceMetadataModel(
                process_instance_id=process_instance.id,
                key=key,
                value=value,
            )
            db.session.add(process_instance_metadata)
            db.session.commit()
        return process_instance

    def assert_report_with_process_metadata_operator_includes_instance(
        self,
        client: FlaskClient,
        user: UserModel,
        process_instance: ProcessInstanceModel,
        operator: str,
        filter_field_value: str = "",
        filters: list[FilterValue] | None = None,
        expect_to_find_instance: bool = True,
    ) -> None:
        if filters is None:
            filters = []

        first_filter: FilterValue = {"field_name": "key1", "field_value": filter_field_value, "operator": operator}
        filters.append(first_filter)
        report_metadata: ReportMetadata = {
            "columns": [
                {"Header": "ID", "accessor": "id", "filterable": False},
                {"Header": "Key one", "accessor": "key1", "filterable": False},
                {"Header": "Key two", "accessor": "key2", "filterable": False},
            ],
            "order_by": ["status"],
            "filter_by": filters,
        }
        process_instance_report = ProcessInstanceReportModel.create_report(
            identifier=f"{process_instance.id}_sure",
            report_metadata=report_metadata,
            user=user,
        )
        response = self.post_to_process_instance_list(client, user, report_metadata=process_instance_report.get_report_metadata())

        if expect_to_find_instance is True:
            assert len(response.json["results"]) == 1
            assert response.json["results"][0]["id"] == process_instance.id
        else:
            if len(response.json["results"]) == 1:
                first_result = response.json["results"][0]
                assert (
                    first_result["id"] != process_instance.id
                ), f"expected not to find a specific process instance, but we found it: {first_result}"
            else:
                assert len(response.json["results"]) == 0
        db.session.delete(process_instance_report)
        db.session.commit()

    def complete_next_manual_task(
        self,
        processor: ProcessInstanceProcessor,
        execution_mode: str | None = None,
        data: dict | None = None,
        user: UserModel | None = None,
    ) -> None:
        user_task = processor.get_ready_user_tasks()[0]
        human_task = HumanTaskModel.query.filter_by(task_guid=str(user_task.id)).first()
        if user is None:
            user = processor.process_instance_model.process_initiator
        ProcessInstanceService.complete_form_task(
            processor=processor,
            spiff_task=user_task,
            data=data or {},
            user=user,
            human_task=human_task,
            execution_mode=execution_mode,
        )

    @contextmanager
    def app_config_mock(self, app: Flask, config_identifier: str, new_config_value: Any) -> Generator:
        initial_value = app.config[config_identifier]
        app.config[config_identifier] = new_config_value
        try:
            yield
        finally:
            app.config[config_identifier] = initial_value

    @staticmethod
    def copy_example_process_models() -> None:
        source = os.path.abspath(os.path.join(FileSystemService.root_path(), "..", "..", "..", "process_models_example_dir"))
        destination = current_app.config["SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR"]
        shutil.copytree(source, destination)

    def round_last_state_change(self, bpmn_process_dict: dict | list) -> None:
        """Round last state change to the nearest 4 significant digits.

        Works around imprecise floating point values in mysql json columns.
        The values between mysql and SpiffWorkflow seem to have minor differences on randomly and since
        we do not care about such precision for this field, round it to a value that is more likely to match.
        """
        if isinstance(bpmn_process_dict, dict):
            for key, value in bpmn_process_dict.items():
                if key == "last_state_change":
                    bpmn_process_dict[key] = round(value, 4)
                elif isinstance(value, dict | list):
                    self.round_last_state_change(value)
        elif isinstance(bpmn_process_dict, list):
            for item in bpmn_process_dict:
                self.round_last_state_change(item)

    def get_test_file(self, *args: str) -> str:
        return os.path.join(current_app.instance_path, "..", "..", "tests", "files", *args)

    def set_timer_event_to_new_time(self, task_model: TaskModel, timedelta_args: dict) -> None:
        new_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(**timedelta_args)
        new_time_formatted = new_time.isoformat()

        new_properties_json = copy.copy(task_model.properties_json)
        new_properties_json["internal_data"]["event_value"]["next"] = new_time_formatted
        task_model.properties_json = new_properties_json
        # make sure we actually commit
        flag_modified(task_model, "properties_json")  # type: ignore
        db.session.add(task_model)
        db.session.commit()
        task_model = TaskModel.query.filter_by(guid=task_model.guid).first()
        assert task_model.properties_json["internal_data"]["event_value"]["next"] == new_time_formatted

    def get_all_children_of_spiff_task(self, spiff_task: SpiffTask) -> list[SpiffTask]:
        children = []
        for child in spiff_task.children:
            children.append(child)
            children += self.get_all_children_of_spiff_task(child)
        return children

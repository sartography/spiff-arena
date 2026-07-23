import logging
import sys
from unittest.mock import patch
from uuid import UUID

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.logging_service import SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR
from spiffworkflow_backend.services.logging_service import SpiffLogHandler
from spiffworkflow_backend.services.logging_service import configure_celery_stdout_logger
from spiffworkflow_backend.services.process_instance_runtime import ProcessInstanceRuntime
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestLoggingService(BaseTest):
    def test_configure_celery_stdout_logger_bypasses_redirected_streams(self) -> None:
        logger = logging.Logger("celery-test")
        logger.addHandler(logging.NullHandler())
        formatter = logging.Formatter("%(message)s")

        configure_celery_stdout_logger(logger, formatter, logging.INFO)

        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert logger.handlers[0].stream is (sys.__stdout__ or sys.stdout)
        assert logger.handlers[0].formatter is formatter
        assert logger.handlers[0].level == logging.INFO
        assert logger.level == logging.INFO
        assert logger.propagate is False

    def test_logger_setup_disables_propagation(self, app: Flask) -> None:
        logger = logging.getLogger("spiffworkflow_backend.services.service_task_delegate")
        assert logger.handlers
        assert logger.propagate is False

    def test_spiff_log_handler_skips_internal_diagnostic_records(self, app: Flask) -> None:
        handler = SpiffLogHandler(app)
        record = logging.LogRecord(
            name="spiff.event",
            level=logging.WARNING,
            pathname=__file__,
            lineno=0,
            msg="diagnostic",
            args=(),
            exc_info=None,
        )
        setattr(record, SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR, True)

        assert handler.filter(record) is False

    def test_socket_failure_warning_marks_record_to_skip_spiff_log_handler(self, app: Flask) -> None:
        handler = SpiffLogHandler(app)

        with patch.object(app.logger, "warning") as warning:
            handler.log_socket_failure(OSError("event stream unavailable"), None)

        warning.assert_called_once()
        extra = warning.call_args.kwargs["extra"]
        assert extra[SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR] is True

    def test_logging_service_detailed_logs(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.principal is not None
        process_model = load_test_spec(
            process_model_id="misc/category_number_one/simple_form",
            process_model_source_directory="simple_form",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = runtime.__class__.get_task_by_bpmn_identifier(human_task.task_name, runtime.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(runtime, spiff_task, {"name": "HEY"}, initiator_user, human_task)

        headers = self.logged_in_headers(with_super_admin_user)
        log_response = client.get(
            f"/v1.0/logs/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance.id}?events=true",
            headers=headers,
        )
        assert log_response.status_code == 200
        assert log_response.json()
        logs: list = log_response.json()["results"]
        assert len(logs) == 4

        for log in logs:
            assert log["process_instance_id"] == process_instance.id
            for key in [
                "event_type",
                "timestamp",
                "spiff_task_guid",
                "bpmn_process_definition_identifier",
                "bpmn_process_definition_name",
                "task_definition_identifier",
                "task_definition_name",
                "bpmn_task_type",
            ]:
                assert key in log.keys()

            if log["task_definition_identifier"] == "Activity_SimpleForm":
                assert log["username"] == initiator_user.username

    def test_logging_service_simple_logs(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        assert initiator_user.principal is not None
        process_model = load_test_spec(
            process_model_id="misc/category_number_one/simple_form",
            process_model_source_directory="simple_form",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        runtime = ProcessInstanceRuntime(process_instance)
        runtime.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = runtime.__class__.get_task_by_bpmn_identifier(human_task.task_name, runtime.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(runtime, spiff_task, {"name": "HEY"}, initiator_user, human_task)

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        runtime = ProcessInstanceRuntime(process_instance)
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = runtime.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(runtime, spiff_manual_task, {}, initiator_user, human_task_one)

        headers = self.logged_in_headers(with_super_admin_user)
        log_response = client.get(
            f"/v1.0/logs/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance.id}?detailed=false",
            headers=headers,
        )
        assert log_response.status_code == 200
        assert log_response.json()
        logs: list = log_response.json()["results"]
        assert len(logs) == 4

        for log in logs:
            assert log["process_instance_id"] == process_instance.id
            assert log["bpmn_task_type"] in ["StartEvent", "EndEvent", "IntermediateThrowEvent"]

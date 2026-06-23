import logging
from unittest.mock import patch
from uuid import UUID

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.logging_service import SPIFF_LOG_HANDLER_SKIP_RECORD_ATTR
from spiffworkflow_backend.services.logging_service import SpiffLogHandler
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestLoggingService(BaseTest):
    def test_logger_setup_disables_propagation(self, app: Flask) -> None:
        logger = logging.getLogger("spiffworkflow_backend.services.service_task_delegate")
        assert logger.handlers
        assert logger.propagate is False

    def test_flask_app_logger_has_handlers(self, app: Flask) -> None:
        logger = logging.getLogger("spiffworkflow_backend")
        assert len(logger.handlers) >= 1
        assert logger.propagate is False

    def test_flask_app_logger_can_output(self, app: Flask) -> None:
        logger = logging.getLogger("spiffworkflow_backend")
        with patch.object(logger.handlers[0], "handle") as mock_handle:
            logger.info("test message")
            mock_handle.assert_called_once()

    def test_celery_worker_logger_setup(self, app: Flask) -> None:
        import os

        from spiffworkflow_backend.services.logging_service import setup_logger_for_app

        os.environ["SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER"] = "true"
        try:
            logger = logging.getLogger("spiffworkflow_backend")

            setup_logger_for_app(app, logging, force_run_with_celery=True)

            assert len(logger.handlers) >= 1
            assert logger.propagate is False
        finally:
            del os.environ["SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER"]

    def test_spiff_task_is_quiet_in_local_dev(self, app: Flask) -> None:
        spiff_task_logger = logging.getLogger("spiff.task")
        assert spiff_task_logger.level in (logging.WARNING, logging.NOTSET)

    def test_spiff_event_is_not_quieted(self, app: Flask) -> None:
        spiff_event_logger = logging.getLogger("spiff.event")
        assert spiff_event_logger.level == logging.NOTSET

    def test_setup_logger_for_app_returns_early_in_celery_worker(self, app: Flask) -> None:
        import os

        from spiffworkflow_backend.services.logging_service import setup_logger_for_app

        os.environ["SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER"] = "true"
        try:
            setup_logger_for_app(app, logging)
            assert True  # no error
        finally:
            del os.environ["SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER"]

    def test_force_run_with_celery_bypasses_early_return(self, app: Flask) -> None:
        import os

        from spiffworkflow_backend.services.logging_service import setup_logger_for_app

        os.environ["SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER"] = "true"
        try:
            logger = logging.getLogger("spiffworkflow_backend")
            setup_logger_for_app(app, logging, force_run_with_celery=True)
            assert len(logger.handlers) >= 1
            assert logger.propagate is False
        finally:
            del os.environ["SPIFFWORKFLOW_BACKEND_RUNNING_IN_CELERY_WORKER"]

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
        AuthorizationService.import_permissions_from_yaml_file()

        process_model = load_test_spec(
            process_model_id="misc/category_number_one/simple_form",
            process_model_source_directory="simple_form",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {"name": "HEY"}, initiator_user, human_task)

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
        AuthorizationService.import_permissions_from_yaml_file()

        process_model = load_test_spec(
            process_model_id="misc/category_number_one/simple_form",
            process_model_source_directory="simple_form",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {"name": "HEY"}, initiator_user, human_task)

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)

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

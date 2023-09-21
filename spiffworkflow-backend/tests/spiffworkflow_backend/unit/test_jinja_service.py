from flask import Flask
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestJinjaService(BaseTest):
    def test_can_sanitize_string(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/manual-task-with-sanitized-markdown",
            process_model_source_directory="manual-task-with-sanitized-markdown",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        task_model = TaskModel.query.filter_by(guid=human_task.task_id).first()
        assert task_model is not None

        expected_result = "\n".join(
            [
                r"* From Filter: Sanitized \| from \| filter",
                r"* From Method Call: Sanitized \| from \| method \| call",
                r"* From ScriptTask: Sanitized \| from \| script \| task",
            ]
        )
        result = JinjaService.render_instructions_for_end_user(task_model)
        assert result == expected_result

        expected_task_data = {
            "from_filter": "Sanitized | from | filter",
            "from_method_call": "Sanitized | from | method | call",
            "from_script_task": "Sanitized \\| from \\| script \\| task",
        }
        assert task_model.get_data() == expected_task_data

    def test_can_render_directly_from_spiff_task(self, app: Flask, with_db_and_bpmn_file_cleanup: None) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/manual-task-with-sanitized-markdown",
            process_model_source_directory="manual-task-with-sanitized-markdown",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        JinjaService.render_instructions_for_end_user(processor.get_all_ready_or_waiting_tasks()[0])
        "\n".join(
            [
                r"* From Filter: Sanitized \| from \| filter",
                r"* From Method Call: Sanitized \| from \| method \| call",
                r"* From ScriptTask: Sanitized \| from \| script \| task",
            ]
        )

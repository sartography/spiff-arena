from flask import Flask
from flask.testing import FlaskClient
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestThreadedExecution(BaseTest):
    def test_four_parallel_script_tasks_that_wait_one_tenth_second(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group("test_group", "test_group")
        process_model = load_test_spec(
            process_model_id="test_group/threads_with_script_timers",
            process_model_source_directory="threads_with_script_timers",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=with_super_admin_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        self.assert_same_start_times(process_instance, "ThreadTask", 4)
        assert processor.bpmn_process_instance.is_completed()
        assert processor.bpmn_process_instance.last_task.data == {"a": 1, "b": 1, "c": 1, "d": 1}

    def test_multi_instance_can_run_in_parallel(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group("test_group", "test_group")
        process_model = load_test_spec(
            process_model_id="test_group/threads_multi_instance",
            process_model_source_directory="threads_multi_instance",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=with_super_admin_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        self.assert_same_start_times(process_instance, "multi", 26)
        assert processor.bpmn_process_instance.is_completed()
        upper_letters = processor.bpmn_process_instance.last_task.data["upper_letters"]
        # Note that Sort is required here, because the threaded execution will complete the list out of order.
        upper_letters.sort()
        assert upper_letters == [
            "A",
            "B",
            "C",
            "D",
            "E",
            "F",
            "G",
            "H",
            "I",
            "J",
            "K",
            "L",
            "M",
            "N",
            "O",
            "P",
            "Q",
            "R",
            "S",
            "T",
            "U",
            "V",
            "W",
            "X",
            "Y",
            "Z",
        ]

    def assert_same_start_times(
        self, process_instance: ProcessInstanceModel, task_name_starts_with: str, expected_size: int
    ) -> None:
        # The start_time recorded for each task should be nearly identical.
        bpmn_process_id = process_instance.bpmn_process_id
        task_models = TaskModel.query.filter_by(bpmn_process_id=bpmn_process_id).all()
        script_tasks = list(
            filter(
                lambda tm: tm.task_definition.bpmn_name is not None
                and tm.task_definition.bpmn_name.startswith(task_name_starts_with),
                task_models,
            )
        )

        assert len(script_tasks) == expected_size
        last_task = None
        for task_model in script_tasks:
            if last_task is None:
                last_task = task_model
                continue
            # Even through the script tasks sleep for .1 second, the difference in start times
            # should be less than 0.001 seconds - they should all start at the same time.
            assert (last_task.start_in_seconds - task_model.start_in_seconds) < 0.001  # type: ignore

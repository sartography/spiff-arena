"""Test_process_instance_processor."""
from uuid import UUID

import pytest
from flask import g
from flask.app import Flask
from flask.testing import FlaskClient
from SpiffWorkflow.task import TaskState  # type: ignore
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.authorization_service import (
    UserDoesNotHaveAccessToTaskError,
)
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceIsAlreadyLockedError,
)
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceLockedBySomethingElseError,
)
from spiffworkflow_backend.services.process_instance_processor import (
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_service import (
    ProcessInstanceService,
)


class TestProcessInstanceProcessor(BaseTest):
    """TestProcessInstanceProcessor."""

    # it's not totally obvious we want to keep this test/file
    def test_script_engine_takes_data_and_returns_expected_results(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_script_engine_takes_data_and_returns_expected_results."""
        app.config["THREAD_LOCAL_DATA"].process_model_identifier = "hey"
        app.config["THREAD_LOCAL_DATA"].process_instance_id = 0
        script_engine = ProcessInstanceProcessor._script_engine

        result = script_engine._evaluate("a", {"a": 1})
        assert result == 1
        app.config["THREAD_LOCAL_DATA"].process_model_identifier = None
        app.config["THREAD_LOCAL_DATA"].process_instance_id = None

    def test_script_engine_can_use_custom_scripts(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Test_script_engine_takes_data_and_returns_expected_results."""
        app.config["THREAD_LOCAL_DATA"].process_model_identifier = "hey"
        app.config["THREAD_LOCAL_DATA"].process_instance_id = 0
        script_engine = ProcessInstanceProcessor._script_engine
        result = script_engine._evaluate("fact_service(type='norris')", {})
        assert (
            result
            == "Chuck Norris doesn’t read books. He stares them down until he gets the"
            " information he wants."
        )
        app.config["THREAD_LOCAL_DATA"].process_model_identifier = None
        app.config["THREAD_LOCAL_DATA"].process_instance_id = None

    def test_sets_permission_correctly_on_human_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_sets_permission_correctly_on_human_task."""
        self.create_process_group(
            client, with_super_admin_user, "test_group", "test_group"
        )
        initiator_user = self.find_or_create_user("initiator_user")
        finance_user = self.find_or_create_user("testuser2")
        assert initiator_user.principal is not None
        assert finance_user.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        finance_group = GroupModel.query.filter_by(identifier="Finance Team").first()
        assert finance_group is not None

        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(
                processor, spiff_task, {}, finance_user, human_task
            )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, initiator_user, human_task
        )

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id == finance_group.id
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == finance_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(
                processor, spiff_task, {}, initiator_user, human_task
            )

        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, finance_user, human_task
        )
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, initiator_user, human_task
        )

        assert process_instance.status == ProcessInstanceStatus.complete.value

    def test_sets_permission_correctly_on_human_task_when_using_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_sets_permission_correctly_on_human_task_when_using_dict."""
        self.create_process_group(
            client, with_super_admin_user, "test_group", "test_group"
        )
        initiator_user = self.find_or_create_user("initiator_user")
        finance_user_three = self.find_or_create_user("testuser3")
        finance_user_four = self.find_or_create_user("testuser4")
        testadmin1 = self.find_or_create_user("testadmin1")
        assert initiator_user.principal is not None
        assert finance_user_three.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        finance_group = GroupModel.query.filter_by(identifier="Finance Team").first()
        assert finance_group is not None

        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes_with_owner_dict.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(
                processor, spiff_task, {}, finance_user_three, human_task
            )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, initiator_user, human_task
        )
        assert human_task.completed_by_user_id == initiator_user.id

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 2
        assert human_task.potential_owners == [finance_user_three, finance_user_four]

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(
                processor, spiff_task, {}, initiator_user, human_task
            )

        g.user = finance_user_three
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, finance_user_three, human_task
        )
        assert human_task.completed_by_user_id == finance_user_three.id
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == finance_user_four

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(
                processor, spiff_task, {}, initiator_user, human_task
            )

        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, finance_user_four, human_task
        )
        assert human_task.completed_by_user_id == finance_user_four.id
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, initiator_user, human_task
        )

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(
                processor, spiff_task, {}, initiator_user, human_task
            )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, testadmin1, human_task
        )

        assert process_instance.status == ProcessInstanceStatus.complete.value

    def test_can_load_up_processor_after_running_model_with_call_activities(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_does_not_recreate_human_tasks_on_multiple_saves."""
        initiator_user = self.find_or_create_user("initiator_user")

        process_model = load_test_spec(
            process_model_id="test_group/call_activity_nested",
            process_model_source_directory="call_activity_nested",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        # ensure this does not raise
        processor = ProcessInstanceProcessor(process_instance)

        # this task will be found within subprocesses
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            "do_nothing", processor.bpmn_process_instance
        )
        assert spiff_task is not None
        assert spiff_task.state == TaskState.COMPLETED

    def test_properly_saves_tasks_when_running(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_does_not_recreate_human_tasks_on_multiple_saves."""
        self.create_process_group(
            client, with_super_admin_user, "test_group", "test_group"
        )
        initiator_user = self.find_or_create_user("initiator_user")
        finance_user_three = self.find_or_create_user("testuser3")
        assert initiator_user.principal is not None
        assert finance_user_three.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        finance_group = GroupModel.query.filter_by(identifier="Finance Team").first()
        assert finance_group is not None

        process_model = load_test_spec(
            process_model_id="test_group/manual_task_with_subprocesses",
            process_model_source_directory="manual_task_with_subprocesses",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert len(process_instance.active_human_tasks) == 1
        initial_human_task_id = process_instance.active_human_tasks[0].id

        # save again to ensure we go attempt to process the human tasks again
        processor.save()

        assert len(process_instance.active_human_tasks) == 1
        assert initial_human_task_id == process_instance.active_human_tasks[0].id

        processor = ProcessInstanceProcessor(process_instance)
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task_one.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(
            processor, spiff_manual_task, {}, initiator_user, human_task_one
        )

        process_instance = ProcessInstanceModel.query.filter_by(
            id=process_instance.id
        ).first()
        processor = ProcessInstanceProcessor(process_instance)
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task(
            UUID(human_task_one.task_id)
        )
        ProcessInstanceService.complete_form_task(
            processor, spiff_manual_task, {}, initiator_user, human_task_one
        )

        # recreate variables to ensure all bpmn json was recreated from scratch from the db
        process_instance_relookup = ProcessInstanceModel.query.filter_by(
            id=process_instance.id
        ).first()
        processor_final = ProcessInstanceProcessor(process_instance_relookup)
        assert process_instance_relookup.status == "complete"

        # first_data_set = {"set_in_top_level_script": 1}
        # second_data_set = {**first_data_set, **{"set_in_top_level_subprocess": 1}}
        # third_data_set = {
        #     **second_data_set,
        #     **{"set_in_test_process_to_call_script": 1},
        # }
        # expected_task_data = {
        #     "top_level_script": first_data_set,
        #     "manual_task": first_data_set,
        #     "top_level_subprocess_script": second_data_set,
        #     "top_level_subprocess": second_data_set,
        #     "test_process_to_call_script": third_data_set,
        #     "top_level_call_activity": third_data_set,
        #     "end_event_of_manual_task_model": third_data_set,
        # }

        all_spiff_tasks = processor_final.bpmn_process_instance.get_tasks()
        assert len(all_spiff_tasks) > 1
        for spiff_task in all_spiff_tasks:
            assert spiff_task.state == TaskState.COMPLETED
            # FIXME: Checking task data cannot work with the feature/remove-loop-reset branch
            #   of SiffWorkflow. This is because it saves script data to the python_env and NOT
            #   to task.data. We may need to either create a new column on TaskModel to put the python_env
            #   data or we could just shove it back onto the task data when adding to the database.
            #   Right now everything works in practice because the python_env data is on the top level workflow
            #   and so is always there but is also always the most recent. If we want to replace spiff_step_details
            #   with TaskModel then we'll need some way to store python_env on each task.
            # spiff_task_name = spiff_task.task_spec.name
            # if spiff_task_name in expected_task_data:
            #     spiff_task_data = expected_task_data[spiff_task_name]
            #     failure_message = (
            #         f"Found unexpected task data on {spiff_task_name}. "
            #         f"Expected: {spiff_task_data}, Found: {spiff_task.data}"
            #     )
            #     assert spiff_task.data == spiff_task_data, failure_message

    def test_does_not_recreate_human_tasks_on_multiple_saves(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_does_not_recreate_human_tasks_on_multiple_saves."""
        self.create_process_group(
            client, with_super_admin_user, "test_group", "test_group"
        )
        initiator_user = self.find_or_create_user("initiator_user")
        finance_user_three = self.find_or_create_user("testuser3")
        assert initiator_user.principal is not None
        assert finance_user_three.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        finance_group = GroupModel.query.filter_by(identifier="Finance Team").first()
        assert finance_group is not None

        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes_with_owner_dict.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert len(process_instance.active_human_tasks) == 1
        initial_human_task_id = process_instance.active_human_tasks[0].id

        # save again to ensure we go attempt to process the human tasks again
        processor.save()

        assert len(process_instance.active_human_tasks) == 1
        assert initial_human_task_id == process_instance.active_human_tasks[0].id

    def test_it_can_lock_and_unlock_a_process_instance(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/model_with_lanes",
            bpmn_file_name="lanes_with_owner_dict.bpmn",
            process_model_source_directory="model_with_lanes",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        assert process_instance.locked_by is None
        assert process_instance.locked_at_in_seconds is None
        processor.lock_process_instance("TEST")

        process_instance = ProcessInstanceModel.query.filter_by(
            id=process_instance.id
        ).first()
        assert process_instance.locked_by is not None
        assert process_instance.locked_at_in_seconds is not None

        with pytest.raises(ProcessInstanceIsAlreadyLockedError):
            processor.lock_process_instance("TEST")

        with pytest.raises(ProcessInstanceLockedBySomethingElseError):
            processor.unlock_process_instance("TEST2")

        processor.unlock_process_instance("TEST")

        process_instance = ProcessInstanceModel.query.filter_by(
            id=process_instance.id
        ).first()
        assert process_instance.locked_by is None
        assert process_instance.locked_at_in_seconds is None

    def test_it_can_loopback_to_previous_bpmn_task_with_gateway(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/loopback_to_manual_task",
            bpmn_file_name="loopback.bpmn",
            process_model_source_directory="loopback_to_manual_task",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=initiator_user
        )
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task_one.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(
            processor, spiff_task, {}, initiator_user, human_task_one
        )

        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 2
        human_task_two = process_instance.active_human_tasks[0]

        # this is just asserting the way the functionality currently works in spiff.
        # we would actually expect this to change one day if we stop reusing the same guid
        # when we re-do a task.
        # assert human_task_two.task_id == human_task_one.task_id

        # EDIT: when using feature/remove-loop-reset branch of SpiffWorkflow, these should be different.
        assert human_task_two.task_id != human_task_one.task_id

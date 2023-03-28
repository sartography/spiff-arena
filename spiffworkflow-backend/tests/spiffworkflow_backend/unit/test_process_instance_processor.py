"""Test_process_instance_processor."""
from uuid import UUID

import pytest
from flask import g
from flask.app import Flask
from flask.testing import FlaskClient
from SpiffWorkflow.task import TaskState  # type: ignore
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
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
    ProcessInstanceProcessor,
)
from spiffworkflow_backend.services.process_instance_queue_service import (
    ProcessInstanceIsAlreadyLockedError,
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
        assert result == "Chuck Norris doesn’t read books. He stares them down until he gets the information he wants."
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
        self.create_process_group_with_api(client, with_super_admin_user, "test_group", "test_group")
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
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user, human_task)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id == finance_group.id
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == finance_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user, human_task)
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        assert process_instance.status == ProcessInstanceStatus.complete.value

    def test_sets_permission_correctly_on_human_task_when_using_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_sets_permission_correctly_on_human_task_when_using_dict."""
        self.create_process_group_with_api(client, with_super_admin_user, "test_group", "test_group")
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
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user_three, human_task)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)
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
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        g.user = finance_user_three
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user_three, human_task)
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
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user_four, human_task)
        assert human_task.completed_by_user_id == finance_user_four.id
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(
            human_task.task_name, processor.bpmn_process_instance
        )
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, testadmin1, human_task)

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
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("do_nothing", processor.bpmn_process_instance)
        assert spiff_task is not None
        assert spiff_task.state == TaskState.COMPLETED

    def test_properly_resets_process_to_given_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group", "test_group")
        initiator_user = self.find_or_create_user("initiator_user")
        finance_user_three = self.find_or_create_user("testuser3")
        assert initiator_user.principal is not None
        assert finance_user_three.principal is not None
        AuthorizationService.import_permissions_from_yaml_file()

        finance_group = GroupModel.query.filter_by(identifier="Finance Team").first()
        assert finance_group is not None

        process_model = load_test_spec(
            process_model_id="test_group/manual_task",
            process_model_source_directory="manual_task",
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

        processor.suspend()
        ProcessInstanceProcessor.reset_process(process_instance, str(spiff_manual_task.parent.id), commit=True)

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        processor.resume()
        processor.do_engine_steps(save=True)
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)
        assert process_instance.status == "complete"

    def test_properly_resets_process_to_given_task_with_call_activity(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group", "test_group")
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
        import pdb; pdb.set_trace()
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

        processor.suspend()
        ProcessInstanceProcessor.reset_process(process_instance, str(spiff_manual_task.parent.id), commit=True)
        import pdb; pdb.set_trace()

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        processor.resume()
        processor.do_engine_steps(save=True)
        import pdb; pdb.set_trace()
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)
        assert process_instance.status == "complete"

    def test_properly_saves_tasks_when_running(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        self.create_process_group_with_api(client, with_super_admin_user, "test_group", "test_group")
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
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)

        # recreate variables to ensure all bpmn json was recreated from scratch from the db
        process_instance_relookup = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor_final = ProcessInstanceProcessor(process_instance_relookup)
        assert process_instance_relookup.status == "complete"

        first_data_set = {"set_in_top_level_script": 1}
        second_data_set = {
            **first_data_set,
            **{"set_in_top_level_subprocess": 1, "we_move_on": False},
        }
        third_data_set = {
            **second_data_set,
            **{
                "set_in_test_process_to_call_script": 1,
                "set_in_test_process_to_call_subprocess_subprocess_script": 1,
                "set_in_test_process_to_call_subprocess_script": 1,
            },
        }
        fourth_data_set = {**third_data_set, **{"a": 1, "we_move_on": True}}
        fifth_data_set = {**fourth_data_set, **{"validate_only": False, "set_top_level_process_script_after_gate": 1}}
        expected_task_data = {
            "top_level_script": first_data_set,
            "manual_task": first_data_set,
            "top_level_subprocess_script": second_data_set,
            "top_level_subprocess": second_data_set,
            "test_process_to_call_subprocess_script": third_data_set,
            "top_level_call_activity": third_data_set,
            "end_event_of_manual_task_model": third_data_set,
            "top_level_subprocess_script_second": fourth_data_set,
            "test_process_to_call_subprocess_script_second": fourth_data_set,
        }

        spiff_tasks_checked_once: list = []

        # TODO: also check task data here from the spiff_task directly to ensure we hydrated spiff correctly
        def assert_spiff_task_is_in_process(spiff_task_identifier: str, bpmn_process_identifier: str) -> None:
            if spiff_task.task_spec.name == spiff_task_identifier:
                expected_task_data_key = spiff_task.task_spec.name
                if spiff_task.task_spec.name in spiff_tasks_checked_once:
                    expected_task_data_key = f"{spiff_task.task_spec.name}_second"

                expected_python_env_data = expected_task_data[expected_task_data_key]

                base_failure_message = (
                    f"Failed on {bpmn_process_identifier} - {spiff_task_identifier} - task data key"
                    f" {expected_task_data_key}."
                )
                task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()

                assert task_model.start_in_seconds is not None
                assert task_model.end_in_seconds is not None
                assert task_model.task_definition_id is not None

                task_definition = task_model.task_definition
                assert task_definition.bpmn_identifier == spiff_task_identifier
                assert task_definition.bpmn_name == spiff_task_identifier.replace("_", " ").title()
                assert task_definition.bpmn_process_definition.bpmn_identifier == bpmn_process_identifier

                message = (
                    f"{base_failure_message} Expected: {sorted(expected_python_env_data)}. Received:"
                    f" {sorted(task_model.json_data())}"
                )
                # TODO: if we split out env data again we will need to use it here instead of json_data
                # assert task_model.python_env_data() == expected_python_env_data, message
                assert task_model.json_data() == expected_python_env_data, message
                spiff_tasks_checked_once.append(spiff_task.task_spec.name)

        all_spiff_tasks = processor_final.bpmn_process_instance.get_tasks()
        assert len(all_spiff_tasks) > 1
        for spiff_task in all_spiff_tasks:
            assert spiff_task.state == TaskState.COMPLETED
            assert_spiff_task_is_in_process(
                "test_process_to_call_subprocess_script", "test_process_to_call_subprocess"
            )
            assert_spiff_task_is_in_process("top_level_subprocess_script", "top_level_subprocess")
            assert_spiff_task_is_in_process("top_level_script", "top_level_process")

            if spiff_task.task_spec.name == "top_level_call_activity":
                # the task id / guid of the call activity gets used as the guid of the bpmn process that it calls
                bpmn_process = BpmnProcessModel.query.filter_by(guid=str(spiff_task.id)).first()
                assert bpmn_process is not None
                bpmn_process_definition = bpmn_process.bpmn_process_definition
                assert bpmn_process_definition is not None
                assert bpmn_process_definition.bpmn_identifier == "test_process_to_call"
                assert bpmn_process_definition.bpmn_name == "Test Process To Call"

            # Check that the direct parent of the called activity subprocess task is the
            #   name of the process that was called from the activity.
            if spiff_task.task_spec.name == "test_process_to_call_subprocess_script":
                task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()
                assert task_model is not None
                bpmn_process = task_model.bpmn_process
                assert bpmn_process is not None
                bpmn_process_definition = bpmn_process.bpmn_process_definition
                assert bpmn_process_definition is not None
                assert bpmn_process_definition.bpmn_identifier == "test_process_to_call_subprocess"
                assert bpmn_process.direct_parent_process_id is not None
                direct_parent_process = BpmnProcessModel.query.filter_by(
                    id=bpmn_process.direct_parent_process_id
                ).first()
                assert direct_parent_process is not None
                assert direct_parent_process.bpmn_process_definition.bpmn_identifier == "test_process_to_call"

        assert processor.get_data() == fifth_data_set

    def test_does_not_recreate_human_tasks_on_multiple_saves(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_does_not_recreate_human_tasks_on_multiple_saves."""
        self.create_process_group_with_api(client, with_super_admin_user, "test_group", "test_group")
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

    # TODO: port this test to queue_service test
    def xxx_test_it_can_lock_and_unlock_a_process_instance(
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

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        assert process_instance.locked_by is not None
        assert process_instance.locked_at_in_seconds is not None

        with pytest.raises(ProcessInstanceIsAlreadyLockedError):
            processor.lock_process_instance("TEST")

        # with pytest.raises(ProcessInstanceLockedBySomethingElseError):
        #    processor.unlock_process_instance("TEST2")

        processor.unlock_process_instance("TEST")

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
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
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task_one)

        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 2
        human_task_two = process_instance.active_human_tasks[0]

        # this is just asserting the way the functionality currently works in spiff.
        # we would actually expect this to change one day if we stop reusing the same guid
        # when we re-do a task.
        # assert human_task_two.task_id == human_task_one.task_id

        # EDIT: when using feature/remove-loop-reset branch of SpiffWorkflow, these should be different.
        assert human_task_two.task_id != human_task_one.task_id

    def test_task_data_is_set_even_if_process_instance_errors(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Test_task_data_is_set_even_if_process_instance_errors."""
        process_model = load_test_spec(
            process_model_id="group/error_with_task_data",
            bpmn_file_name="script_error_with_task_data.bpmn",
            process_model_source_directory="error",
        )
        process_instance = self.create_process_instance_from_process_model(
            process_model=process_model, user=with_super_admin_user
        )

        processor = ProcessInstanceProcessor(process_instance)
        with pytest.raises(ApiError):
            processor.do_engine_steps(save=True)

        process_instance_final = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor_final = ProcessInstanceProcessor(process_instance_final)

        spiff_task = processor_final.get_task_by_bpmn_identifier(
            "script_task_two", processor_final.bpmn_process_instance
        )
        assert spiff_task is not None
        assert spiff_task.state == TaskState.WAITING
        assert spiff_task.data == {"my_var": "THE VAR"}

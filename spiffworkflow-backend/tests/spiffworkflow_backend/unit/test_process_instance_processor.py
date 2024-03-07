from uuid import UUID

import pytest
from flask import g
from flask.app import Flask
from flask.testing import FlaskClient
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore
from SpiffWorkflow.util.task import TaskState  # type: ignore
from spiffworkflow_backend.exceptions.error import UserDoesNotHaveAccessToTaskError
from spiffworkflow_backend.models.bpmn_process import BpmnProcessModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceStatus
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventModel
from spiffworkflow_backend.models.process_instance_event import ProcessInstanceEventType
from spiffworkflow_backend.models.task import TaskModel  # noqa: F401
from spiffworkflow_backend.models.task_definition import TaskDefinitionModel
from spiffworkflow_backend.models.task_instructions_for_end_user import TaskInstructionsForEndUserModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.workflow_execution_service import WorkflowExecutionServiceError

from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestProcessInstanceProcessor(BaseTest):
    def test_script_engine_can_use_custom_scripts(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/random_fact",
            bpmn_file_name="random_fact_set.bpmn",
            process_model_source_directory="random_fact",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert process_instance.status == ProcessInstanceStatus.complete.value
        process_data = processor.get_data()
        assert process_data is not None
        assert "FactService" in process_data
        assert (
            process_data["FactService"]
            == "Chuck Norris doesn’t read books. He stares them down until he gets the information he wants."
        )

    def test_sets_permission_correctly_on_human_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
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
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user, human_task)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id == finance_group.id
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == finance_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user, human_task)
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        assert process_instance.status == ProcessInstanceStatus.complete.value

    def test_sets_permission_correctly_on_human_task_when_using_dict(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
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
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user_three, human_task)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)
        assert human_task.completed_by_user_id == initiator_user.id

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id == finance_group.id
        assert len(human_task.potential_owners) == 2
        assert human_task.potential_owners == [finance_user_three, finance_user_four]

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        g.user = finance_user_three
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user_three, human_task)
        assert human_task.completed_by_user_id == finance_user_three.id
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id == finance_group.id
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == finance_user_four

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, finance_user_four, human_task)
        assert human_task.completed_by_user_id == finance_user_four.id
        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        assert human_task.lane_assignment_id is None
        assert len(human_task.potential_owners) == 1
        assert human_task.potential_owners[0] == initiator_user

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)

        assert len(process_instance.active_human_tasks) == 1
        human_task = process_instance.active_human_tasks[0]
        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task.task_name, processor.bpmn_process_instance)
        with pytest.raises(UserDoesNotHaveAccessToTaskError):
            ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, testadmin1, human_task)

        assert process_instance.status == ProcessInstanceStatus.complete.value

    def test_can_load_up_processor_after_running_model_with_call_activities(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")

        process_model = load_test_spec(
            process_model_id="test_group/call_activity_nested",
            process_model_source_directory="call_activity_nested",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        # ensure this does not raise
        processor = ProcessInstanceProcessor(process_instance)

        # this task will be found within subprocesses
        spiff_task = processor.__class__.get_task_by_bpmn_identifier("level_3_script_task", processor.bpmn_process_instance)
        assert spiff_task is not None
        assert spiff_task.state == TaskState.COMPLETED

    def test_properly_resets_process_to_given_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
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
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
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
        assert spiff_manual_task is not None
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)

        processor.suspend()
        ProcessInstanceProcessor.reset_process(process_instance, str(spiff_manual_task.id))

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        processor.resume()
        processor.do_engine_steps(save=True)

        # if if there are more human tasks then they were duplicated in the reset process method
        assert len(process_instance.human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)
        assert process_instance.status == "complete"

    # this test has been failing intermittently for some time on windows, perhaps ever since it was first added
    def test_properly_resets_process_to_given_task_with_call_activity(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
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
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert len(process_instance.active_human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]
        initial_human_task_id = human_task_one.id
        assert len(process_instance.active_human_tasks) == 1
        assert initial_human_task_id == process_instance.active_human_tasks[0].id
        assert len(process_instance.human_tasks) == 1

        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        assert len(process_instance.active_human_tasks) == 1, "expected 1 active human task"

        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)
        assert len(process_instance.human_tasks) == 2, "expected 2 human tasks after first one is completed"
        assert len(process_instance.active_human_tasks) == 1, "expected 1 active human tasks after 1st one is completed"

        # unnecessary lookup just in case on windows
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()

        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)
        assert (
            len(process_instance.active_human_tasks) == 1
        ), "expected 1 active human tasks after 2nd one is completed, as we have looped back around."

        processor.suspend()

        all_task_models_matching_top_level_subprocess_script = (
            TaskModel.query.join(TaskDefinitionModel)
            .filter(TaskDefinitionModel.bpmn_identifier == "top_level_subprocess_script")
            .all()
        )
        assert len(all_task_models_matching_top_level_subprocess_script) == 1
        task_model_to_reset_to = all_task_models_matching_top_level_subprocess_script[0]
        assert task_model_to_reset_to is not None
        assert len(process_instance.human_tasks) == 3, "expected 3 human tasks before reset"
        processor = ProcessInstanceProcessor(process_instance)
        processor = ProcessInstanceProcessor(process_instance)
        ProcessInstanceProcessor.reset_process(process_instance, task_model_to_reset_to.guid)
        assert len(process_instance.human_tasks) == 2, "still expected 2 human tasks after reset"

        # make sure sqlalchemy session matches current db state
        db.session.expire_all()
        assert len(process_instance.human_tasks) == 2, "still expected 3 human tasks after reset and session expire_all"

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)

        # make sure we did actually reset to the task we expected
        ready_or_waiting_tasks = processor.get_all_ready_or_waiting_tasks()
        top_level_subprocess_script_spiff_task = next(
            task for task in ready_or_waiting_tasks if task.task_spec.name == "top_level_subprocess_script"
        )
        assert top_level_subprocess_script_spiff_task is not None
        processor.resume()
        assert (
            len(process_instance.human_tasks) == 2
        ), "expected 2 human tasks after resume since resume does not do anything in that regard"
        ready_or_waiting_tasks = processor.get_all_ready_or_waiting_tasks()
        assert len(ready_or_waiting_tasks) == 2
        ready_or_waiting_task_identifiers = [t.task_spec.name for t in ready_or_waiting_tasks]
        assert sorted(["top_level_subprocess_script", "top_level_subprocess"]) == sorted(ready_or_waiting_task_identifiers)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        ready_or_waiting_tasks = processor.get_all_ready_or_waiting_tasks()
        assert len(ready_or_waiting_tasks) == 1

        # this assertion is failing intermittently on windows
        # it's top_level_subprocess on windows sometimes
        assert ready_or_waiting_tasks[0].task_spec.name == "top_level_manual_task_two"

        # this assertion is failing intermittently on windows
        assert len(process_instance.human_tasks) == 3, "expected 3 human tasks after reset and do_engine_steps"

        spiff_task_guid_strings = [ht.task_id for ht in process_instance.human_tasks]
        unique_task_guids = set(spiff_task_guid_strings)
        assert len(unique_task_guids) == 3, "expected 3 unique task guids after reset and do_engine_steps"

        # reload again, just in case, since the assertion where it says there should be 1 active_human_task
        # is failing intermittently on windows, so just debugging.
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        assert len(process_instance.active_human_tasks) == 1

        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        assert process_instance.status == "complete"

    def test_properly_resets_process_on_tasks_with_boundary_events(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
        process_model = load_test_spec(
            process_model_id="test_group/boundary_event_reset",
            process_model_source_directory="boundary_event_reset",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert len(process_instance.active_human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(
            processor, spiff_manual_task, {}, process_instance.process_initiator, human_task_one
        )
        assert len(process_instance.active_human_tasks) == 1, "expected 1 active human tasks after 2nd one is completed"
        assert process_instance.active_human_tasks[0].task_title == "Final"

        # Reset the process back to the task within the call activity that contains a timer_boundary event.
        reset_to_spiff_task: SpiffTask = processor.__class__.get_task_by_bpmn_identifier(
            "manual_task_1", processor.bpmn_process_instance
        )
        processor.suspend()
        processor = ProcessInstanceProcessor(process_instance)
        ProcessInstanceProcessor.reset_process(process_instance, str(reset_to_spiff_task.id))
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        human_task_one = process_instance.active_human_tasks[0]
        assert human_task_one.task_title == "Manual Task #1"
        processor = ProcessInstanceProcessor(process_instance)
        processor.manual_complete_task(str(human_task_one.task_id), execute=True, user=process_instance.process_initiator)
        processor = ProcessInstanceProcessor(process_instance)
        processor.resume()
        processor.do_engine_steps(save=True)
        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()

        assert len(process_instance.active_human_tasks) == 1
        assert process_instance.active_human_tasks[0].task_title == "Final", (
            "once we reset, resume, and complete the task, we should be back to the Final step again, and not"
            "stuck waiting for the call activity to complete (which was happening in a bug I'm fixing right now)"
        )

        task_event = ProcessInstanceEventModel.query.filter_by(
            task_guid=human_task_one.task_id, event_type=ProcessInstanceEventType.task_executed_manually.value
        ).first()
        assert task_event is not None

    def test_step_through_gateway(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
        process_model = load_test_spec(
            process_model_id="test_group/step_through_gateway",
            process_model_source_directory="step_through_gateway",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert len(process_instance.active_human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]
        processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        processor.manual_complete_task(str(human_task_one.task_id), execute=True, user=process_instance.process_initiator)
        processor.save()
        processor = ProcessInstanceProcessor(process_instance)
        step1_task = processor.get_task_by_bpmn_identifier("step_1", processor.bpmn_process_instance)
        assert step1_task is not None
        assert step1_task.state == TaskState.COMPLETED
        gateway_task = processor.get_task_by_bpmn_identifier("Gateway_Open", processor.bpmn_process_instance)
        assert gateway_task is not None
        assert gateway_task.state == TaskState.READY

        gateway_task = processor.bpmn_process_instance.get_tasks(state=TaskState.READY)[0]
        processor.manual_complete_task(str(gateway_task.id), execute=True, user=process_instance.process_initiator)
        processor.save()
        processor = ProcessInstanceProcessor(process_instance)
        gateway_task = processor.get_task_by_bpmn_identifier("Gateway_Open", processor.bpmn_process_instance)
        assert gateway_task is not None
        assert gateway_task.state == TaskState.COMPLETED

        task_event = ProcessInstanceEventModel.query.filter_by(
            task_guid=str(gateway_task.id), event_type=ProcessInstanceEventType.task_executed_manually.value
        ).first()
        assert task_event is not None

    def test_properly_saves_tasks_when_running(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
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
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
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
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(processor, spiff_manual_task, {}, initiator_user, human_task_one)

        # recreate variables to ensure all bpmn json was recreated from scratch from the db
        process_instance_relookup = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor_final = ProcessInstanceProcessor(process_instance_relookup)
        processor_final.do_engine_steps(save=True, execution_strategy_name="greedy")

        assert process_instance_relookup.status == "complete"

        data_set_1 = {"set_in_top_level_script": 1}
        data_set_2 = {
            **data_set_1,
            **{"set_in_top_level_subprocess": 1, "we_move_on": False},
        }
        data_set_3 = {
            **data_set_2,
            **{
                "set_in_test_process_to_call_subprocess_subprocess_script": 1,
                "set_in_test_process_to_call_subprocess_script": 1,
            },
        }
        data_set_4 = {
            **data_set_3,
            **{
                "set_in_test_process_to_call_script": 1,
            },
        }
        data_set_5 = {**data_set_4, **{"a": 1, "we_move_on": True}}
        data_set_6 = {**data_set_5, **{"set_top_level_process_script_after_gate": 1}}
        data_set_7 = {**data_set_6, **{"validate_only": False, "set_top_level_process_script_after_gate": 1}}
        expected_task_data = {
            "top_level_script": {"data": data_set_1, "bpmn_process_identifier": "top_level_process"},
            "top_level_manual_task_one": {"data": data_set_1, "bpmn_process_identifier": "top_level_process"},
            "top_level_manual_task_two": {"data": data_set_1, "bpmn_process_identifier": "top_level_process"},
            "top_level_subprocess_script": {
                "data": data_set_2,
                "bpmn_process_identifier": "top_level_subprocess",
            },
            "top_level_subprocess": {"data": data_set_2, "bpmn_process_identifier": "top_level_process"},
            "test_process_to_call_subprocess_script": {
                "data": data_set_3,
                "bpmn_process_identifier": "test_process_to_call_subprocess",
            },
            "top_level_call_activity": {"data": data_set_4, "bpmn_process_identifier": "top_level_process"},
            "top_level_manual_task_two_second": {
                "data": data_set_4,
                "bpmn_process_identifier": "top_level_process",
            },
            "top_level_subprocess_script_second": {
                "data": data_set_5,
                "bpmn_process_identifier": "top_level_subprocess",
            },
            "top_level_subprocess_second": {"data": data_set_5, "bpmn_process_identifier": "top_level_process"},
            "test_process_to_call_subprocess_script_second": {
                "data": data_set_5,
                "bpmn_process_identifier": "test_process_to_call_subprocess",
            },
            "top_level_call_activity_second": {
                "data": data_set_5,
                "bpmn_process_identifier": "top_level_process",
            },
            "end_event_of_manual_task_model": {"data": data_set_6, "bpmn_process_identifier": "top_level_process"},
        }

        spiff_tasks_checked: list[str] = []

        # TODO: also check task data here from the spiff_task directly to ensure we hydrated spiff correctly
        def assert_spiff_task_is_in_process(spiff_task: SpiffTask) -> None:
            spiff_task_identifier = spiff_task.task_spec.name
            if spiff_task_identifier in expected_task_data:
                bpmn_process_identifier = expected_task_data[spiff_task_identifier]["bpmn_process_identifier"]
                expected_task_data_key = spiff_task_identifier
                if spiff_task_identifier in spiff_tasks_checked:
                    expected_task_data_key = f"{spiff_task.task_spec.name}_second"

                assert expected_task_data_key not in spiff_tasks_checked

                spiff_tasks_checked.append(expected_task_data_key)

                expected_python_env_data = expected_task_data[expected_task_data_key]["data"]

                base_failure_message = (
                    f"Failed on {bpmn_process_identifier} - {spiff_task_identifier} - task data key {expected_task_data_key}."
                )

                count_failure_message = (
                    f"{base_failure_message} There are more than 2 entries of this task in the db."
                    " There should only ever be max 2."
                )
                task_models_with_bpmn_identifier_count = (
                    TaskModel.query.join(TaskDefinitionModel)
                    .filter(TaskModel.process_instance_id == process_instance_relookup.id)
                    .filter(TaskDefinitionModel.bpmn_identifier == spiff_task.task_spec.name)
                    .count()
                )

                # some tasks will have 2 COMPLETED and 1 LIKELY/MAYBE
                assert task_models_with_bpmn_identifier_count < 4, count_failure_message
                task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()

                assert task_model.start_in_seconds is not None
                assert task_model.end_in_seconds is not None
                assert task_model.task_definition_id is not None

                task_definition = task_model.task_definition
                assert task_definition.bpmn_identifier == spiff_task_identifier
                assert task_definition.bpmn_name == spiff_task_identifier.replace("_", " ").title()
                assert task_definition.bpmn_process_definition.bpmn_identifier == bpmn_process_identifier, base_failure_message

                message = (
                    f"{base_failure_message} Expected: {sorted(expected_python_env_data)}. Received:"
                    f" {sorted(task_model.json_data())}"
                )
                # TODO: if we split out env data again we will need to use it here instead of json_data
                # assert task_model.python_env_data() == expected_python_env_data, message
                assert task_model.json_data() == expected_python_env_data, message

        all_spiff_tasks = processor_final.bpmn_process_instance.get_tasks()
        assert len(all_spiff_tasks) > 1
        for spiff_task in all_spiff_tasks:
            if spiff_task.task_spec.name == "our_boundary_event":
                assert spiff_task.state == TaskState.CANCELLED
                spiff_tasks_checked.append(spiff_task.task_spec.name)
                continue

            assert spiff_task.state == TaskState.COMPLETED
            assert_spiff_task_is_in_process(spiff_task)

            if spiff_task.task_spec.name == "top_level_call_activity":
                # the task id / guid of the call activity gets used as the guid of the bpmn process that it calls
                bpmn_process = BpmnProcessModel.query.filter_by(guid=str(spiff_task.id)).first()
                assert bpmn_process is not None
                bpmn_process_definition = bpmn_process.bpmn_process_definition
                assert bpmn_process_definition is not None
                assert bpmn_process_definition.bpmn_identifier == "test_process_to_call"
                assert bpmn_process_definition.bpmn_name == "Test Process To Call"
                spiff_tasks_checked.append(spiff_task.task_spec.name)

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
                direct_parent_process = BpmnProcessModel.query.filter_by(id=bpmn_process.direct_parent_process_id).first()
                assert direct_parent_process is not None
                assert direct_parent_process.bpmn_process_definition.bpmn_identifier == "test_process_to_call"
                spiff_tasks_checked.append(spiff_task.task_spec.name)

        expected_task_identifiers = list(expected_task_data.keys()) + [
            "our_boundary_event",
            "test_process_to_call_subprocess_script",
            "top_level_call_activity",
        ]
        for task_bpmn_identifier in expected_task_identifiers:
            message = (
                f"Expected to have seen a task with a bpmn_identifier of {task_bpmn_identifier} but did not. "
                f"Only saw {sorted(spiff_tasks_checked)}"
            )
            assert task_bpmn_identifier in spiff_tasks_checked, message

        task_models_that_are_predicted_count = (
            TaskModel.query.filter(TaskModel.process_instance_id == process_instance_relookup.id)
            .filter(TaskModel.state.in_(["LIKELY", "MAYBE"]))  # type: ignore
            .count()
        )
        assert task_models_that_are_predicted_count == 4
        assert processor_final.get_data() == data_set_7

    def test_does_not_recreate_human_tasks_on_multiple_saves(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        self.create_process_group("test_group", "test_group")
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
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert len(process_instance.active_human_tasks) == 1
        initial_human_task_id = process_instance.active_human_tasks[0].id

        # save again to ensure we go attempt to process the human tasks again
        processor.save()

        assert len(process_instance.active_human_tasks) == 1
        assert initial_human_task_id == process_instance.active_human_tasks[0].id

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
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]

        spiff_task = processor.__class__.get_task_by_bpmn_identifier(human_task_one.task_name, processor.bpmn_process_instance)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task_one)

        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 2
        human_task_two = process_instance.active_human_tasks[0]

        assert human_task_two.task_id != human_task_one.task_id

    def test_it_can_loopback_to_previous_bpmn_subprocess_with_gateway(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        initiator_user = self.find_or_create_user("initiator_user")
        process_model = load_test_spec(
            process_model_id="test_group/loopback_to_subprocess",
            process_model_source_directory="loopback_to_subprocess",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model, user=initiator_user)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")

        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 1
        human_task_one = process_instance.active_human_tasks[0]

        spiff_task = processor.get_task_by_guid(human_task_one.task_id)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task_one)

        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 2
        human_task_two = process_instance.active_human_tasks[0]
        spiff_task = processor.get_task_by_guid(human_task_two.task_id)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task_two)

        # ensure this does not raise a KeyError
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="greedy")
        assert len(process_instance.active_human_tasks) == 1
        assert len(process_instance.human_tasks) == 3
        human_task_three = process_instance.active_human_tasks[0]
        spiff_task = processor.get_task_by_guid(human_task_three.task_id)
        ProcessInstanceService.complete_form_task(processor, spiff_task, {}, initiator_user, human_task_three)

    def test_task_data_is_set_even_if_process_instance_errors_and_creates_task_failed_event(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="group/error_with_task_data",
            bpmn_file_name="script_error_with_task_data.bpmn",
            process_model_source_directory="error",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)

        processor = ProcessInstanceProcessor(process_instance)
        with pytest.raises(WorkflowExecutionServiceError):
            processor.do_engine_steps(save=True)

        process_instance_final = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor_final = ProcessInstanceProcessor(process_instance_final)

        spiff_task = processor_final.get_task_by_bpmn_identifier("script_task_two", processor_final.bpmn_process_instance)
        assert spiff_task is not None
        task_model = TaskModel.query.filter_by(guid=str(spiff_task.id)).first()
        assert task_model is not None
        assert task_model.state == "ERROR"
        assert task_model.get_data() == {"my_var": "THE VAR"}

        process_instance_events = process_instance.process_instance_events
        assert len(process_instance_events) == 4
        error_events = [e for e in process_instance_events if e.event_type == ProcessInstanceEventType.task_failed.value]
        assert len(error_events) == 1
        error_event = error_events[0]
        assert error_event.task_guid is not None
        process_instance_error_details = error_event.error_details
        assert len(process_instance_error_details) == 1
        error_detail = process_instance_error_details[0]
        assert error_detail.message == "NameError:name 'hey' is not defined.  Did you mean 'my_var'?"
        assert error_detail.task_offset is None
        assert error_detail.task_line_number == 1
        assert error_detail.task_line_contents == "hey"
        assert error_detail.task_trace is not None

    def test_can_complete_task_with_call_activity_after_manual_task(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="group/call_activity_with_manual_task",
            process_model_source_directory="call_activity_with_manual_task",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)

        process_instance = ProcessInstanceModel.query.filter_by(id=process_instance.id).first()
        processor = ProcessInstanceProcessor(process_instance)
        human_task_one = process_instance.active_human_tasks[0]
        spiff_manual_task = processor.bpmn_process_instance.get_task_from_id(UUID(human_task_one.task_id))
        ProcessInstanceService.complete_form_task(
            processor, spiff_manual_task, {}, process_instance.process_initiator, human_task_one
        )

    def test_can_store_instructions_for_end_user(
        self,
        app: Flask,
        client: FlaskClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            process_model_id="test_group/script_task_with_instruction",
            bpmn_file_name="script_task_with_instruction.bpmn",
            process_model_source_directory="script-task-with-instruction",
        )
        process_instance = self.create_process_instance_from_process_model(process_model=process_model)

        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True, execution_strategy_name="queue_instructions_for_end_user")
        user_instructions = TaskInstructionsForEndUserModel.entries_for_process_instance(process_instance.id)
        assert len(user_instructions) == 1
        assert user_instructions[0].instruction == "We run script one"
        processor.do_engine_steps(execution_strategy_name="run_current_ready_tasks")

        processor.do_engine_steps(save=True, execution_strategy_name="queue_instructions_for_end_user")
        user_instructions = TaskInstructionsForEndUserModel.entries_for_process_instance(process_instance.id)
        assert len(user_instructions) == 2
        # ensure ordering is correct
        assert user_instructions[0].instruction == "We run script two"

        assert process_instance.status == ProcessInstanceStatus.running.value
        processor.do_engine_steps(execution_strategy_name="run_current_ready_tasks")
        assert process_instance.status == ProcessInstanceStatus.running.value
        processor.do_engine_steps(save=True, execution_strategy_name="queue_instructions_for_end_user")
        assert process_instance.status == ProcessInstanceStatus.complete.value

        remaining_entries = TaskInstructionsForEndUserModel.query.all()
        assert len(remaining_entries) == 2
        user_instruction_list = TaskInstructionsForEndUserModel.retrieve_and_clear(process_instance.id)
        user_instruction_strings = [ui.instruction for ui in user_instruction_list]
        assert user_instruction_strings == ["We run script two", "We run script one"]
        remaining_entries = TaskInstructionsForEndUserModel.query.all()
        assert len(remaining_entries) == 2
        for entry in remaining_entries:
            assert entry.has_been_retrieved is True

        db.session.delete(process_instance)
        db.session.commit()

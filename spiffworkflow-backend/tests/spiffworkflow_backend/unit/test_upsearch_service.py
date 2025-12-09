from unittest.mock import MagicMock
from unittest.mock import patch

from spiffworkflow.exceptions import WorkflowException  # type: ignore

from spiffworkflow_backend.data_stores.json import JSONDataStoreModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_model import ProcessModel  # type: ignore
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService
from spiffworkflow_backend.services.upsearch_service import UpsearchService
from spiffworkflow_backend.services.workflow_service import WorkflowService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestUpsearchService(BaseTest):
    CALLER_BPMN = """<?xml version="1.0" encoding="UTF-8"?>
    <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                      xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                      xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                      xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                      id="Definitions_1" targetNamespace="http://bpmn.io/schema|bpmn">
      <bpmn:process id="caller_ds_scope_test" isExecutable="true">
        <bpmn:startEvent id="StartEvent_1"/>
        <bpmn:callActivity id="CallActivity_1" calledElement="callee_ds_scope_test" />
        <bpmn:endEvent id="EndEvent_1"/>
        <bpmn:sequenceFlow id="SequenceFlow_1" sourceRef="StartEvent_1" targetRef="CallActivity_1" />
        <bpmn:sequenceFlow id="SequenceFlow_2" sourceRef="CallActivity_1" targetRef="EndEvent_1" />
      </bpmn:process>
    </bpmn:definitions>
    """

    CALLEE_BPMN = """<?xml version="1.0" encoding="UTF-8"?>
    <bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
                      xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI"
                      xmlns:dc="http://www.omg.org/spec/DD/20100524/DC"
                      xmlns:di="http://www.omg.org/spec/DD/20100524/DI"
                      id="Definitions_1" targetNamespace="http://bpmn.io/schema|bpmn">
      <bpmn:process id="callee_ds_scope_test" isExecutable="true">
        <bpmn:scriptTask id="script_task" scriptFormat="python">
          <bpmn:script>value = my_data_store['some_key']</bpmn:script>
        </bpmn:scriptTask>
        <bpmn:dataStoreReference id="dataStoreReference" dataStoreRef="myDataStore" />
        <bpmn:association id="association" sourceRef="dataStoreReference" targetRef="script_task" />
        <bpmn:startEvent id="StartEvent_1"/>
        <bpmn:endEvent id="EndEvent_1"/>
        <bpmn:sequenceFlow id="SequenceFlow_1" sourceRef="StartEvent_1" targetRef="script_task" />
        <bpmn:sequenceFlow id="SequenceFlow_2" sourceRef="script_task" targetRef="EndEvent_1" />
      </bpmn:process>
      <bpmn:dataStore id="myDataStore" name="my_data_store" />
    </bpmn:definitions>
    """

    def test_upsearch_locations(self) -> None:
        locations = UpsearchService.upsearch_locations("misc/jonjon/generic-data-store-area/test-level-2")
        assert locations == [
            "misc/jonjon/generic-data-store-area/test-level-2",
            "misc/jonjon/generic-data-store-area",
            "misc/jonjon",
            "misc",
            "",
        ]

    @patch("spiffworkflow_backend.services.process_model_service.ProcessModelService")
    def test_called_process_uses_own_group_for_scope(self, mock_pm_service: MagicMock) -> None:
        """
        Tests that a called process uses its own process group for data store
        searches, not the calling process's group.
        """
        caller_process_model = ProcessModel(
            id=1, name="caller_ds_scope_test", process_group_id="site-administration", bpmn_bytes=self.CALLER_BPMN.encode()
        )
        callee_process_model = ProcessModel(
            id=2, name="callee_ds_scope_test", process_group_id="finance", bpmn_bytes=self.CALLEE_BPMN.encode()
        )

        def get_process_model_from_workflow_mock(workflow_spec_id: str, version_id: str | None = None) -> ProcessModel | None:
            if workflow_spec_id == "caller_ds_scope_test":
                return caller_process_model
            if workflow_spec_id == "callee_ds_scope_test":
                return callee_process_model
            return None

        mock_pm_service.get_process_model_from_workflow.side_effect = get_process_model_from_workflow_mock
        mock_user = MagicMock()

        # Case 1: Data store is in the callee's process group ('finance').
        # The workflow should succeed as the data store is in scope.
        ds_finance = JSONDataStoreModel(
            identifier="my_data_store", location="finance", name="Finance Data Store", schema={}, description=""
        )
        ds_finance.data = {"some_key": "finance_value"}
        db.session.add(ds_finance)
        db.session.commit()

        workflow = WorkflowService.get_workflow(caller_process_model)  # type: ignore
        process_instance_service = ProcessInstanceService()
        process_instance_service.create_process_instance(workflow, mock_user)
        workflow.run_all_tasks()
        assert workflow.data["value"] == "finance_value"

        db.session.delete(ds_finance)
        db.session.commit()

        # Case 2: Data store is in the caller's process group ('site-administration').
        # The workflow should fail as the data store is out of scope for the callee.
        ds_admin = JSONDataStoreModel(
            identifier="my_data_store", location="site-administration", name="Admin Data Store", schema={}, description=""
        )
        ds_admin.data = {"some_key": "admin_value"}
        db.session.add(ds_admin)
        db.session.commit()

        workflow = WorkflowService.get_workflow(caller_process_model)  # type: ignore
        process_instance_service.create_process_instance(workflow, mock_user)
        try:
            workflow.run_all_tasks()
            raise AssertionError("WorkflowException was not raised")
        except WorkflowException:
            pass

        db.session.delete(ds_admin)
        db.session.commit()

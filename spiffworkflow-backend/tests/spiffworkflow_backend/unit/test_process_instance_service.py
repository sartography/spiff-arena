from datetime import datetime
from datetime import timezone

from flask.app import Flask
from SpiffWorkflow.bpmn.event import PendingBpmnEvent  # type: ignore
from spiffworkflow_backend.models.process_instance_file_data import ProcessInstanceFileDataModel
from spiffworkflow_backend.services.process_instance_service import ProcessInstanceService

from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestProcessInstanceService(BaseTest):
    SAMPLE_FILE_DATA = "data:some/mimetype;name=testing.txt;base64,dGVzdGluZwo="
    SAMPLE_DIGEST_REFERENCE = f"data:some/mimetype;name=testing.txt;base64,{ProcessInstanceService.FILE_DATA_DIGEST_PREFIX}12a61f4e173fb3a11c05d6471f74728f76231b4a5fcd9667cef3af87a3ae4dc2"  # noqa: B950,E501

    def _check_sample_file_data_model(
        self,
        identifier: str,
        list_index: int | None,
        model: ProcessInstanceFileDataModel | None,
    ) -> None:
        assert model is not None
        assert model.identifier == identifier
        assert model.process_instance_id == 111
        assert model.list_index == list_index
        assert model.mimetype == "some/mimetype"
        assert model.filename == "testing.txt"
        assert model.contents == b"testing\n"  # type: ignore
        assert model.digest == "12a61f4e173fb3a11c05d6471f74728f76231b4a5fcd9667cef3af87a3ae4dc2"

    def test_can_create_file_data_model_for_file_data_value(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        model = ProcessInstanceService.file_data_model_for_value(
            "uploaded_file",
            self.SAMPLE_FILE_DATA,
            111,
        )
        self._check_sample_file_data_model("uploaded_file", None, model)

    def test_does_not_create_file_data_model_for_non_file_data_value(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        model = ProcessInstanceService.file_data_model_for_value(
            "not_a_file",
            "just a value",
            111,
        )
        assert model is None

    def test_can_create_file_data_models_for_single_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "uploaded_file": self.SAMPLE_FILE_DATA,
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 1
        self._check_sample_file_data_model("uploaded_file", None, models[0])

    def test_can_create_file_data_models_for_multiple_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 2
        self._check_sample_file_data_model("uploaded_files", 0, models[0])
        self._check_sample_file_data_model("uploaded_files", 1, models[1])

    def test_can_create_file_data_models_for_mix_of_file_data_and_non_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "not_a_file": "just a value",
            "uploaded_file": self.SAMPLE_FILE_DATA,
            "not_a_file2": "just a value 2",
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
            "not_a_file3": "just a value 3",
            "uploaded_files2": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
            "uploaded_file2": self.SAMPLE_FILE_DATA,
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 6
        self._check_sample_file_data_model("uploaded_file", None, models[0])
        self._check_sample_file_data_model("uploaded_files", 0, models[1])
        self._check_sample_file_data_model("uploaded_files", 1, models[2])
        self._check_sample_file_data_model("uploaded_files2", 0, models[3])
        self._check_sample_file_data_model("uploaded_files2", 1, models[4])
        self._check_sample_file_data_model("uploaded_file2", None, models[5])

    def test_does_not_create_file_data_models_for_non_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "not_a_file": "just a value",
            "also_no_files": ["not a file", "also not a file"],
            "still_no_files": [{"key": "value"}],
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 0

    def test_can_replace_file_data_values_with_digest_references(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "uploaded_file": self.SAMPLE_FILE_DATA,
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)
        ProcessInstanceService.replace_file_data_with_digest_references(data, models)

        assert data == {
            "uploaded_file": self.SAMPLE_DIGEST_REFERENCE,
            "uploaded_files": [
                self.SAMPLE_DIGEST_REFERENCE,
                self.SAMPLE_DIGEST_REFERENCE,
            ],
        }

    def test_does_not_replace_non_file_data_values_with_digest_references(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "not_a_file": "just a value",
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)
        ProcessInstanceService.replace_file_data_with_digest_references(data, models)

        assert len(data) == 1
        assert data["not_a_file"] == "just a value"

    def test_can_replace_file_data_values_with_digest_references_when_non_file_data_values_are_present(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "not_a_file": "just a value",
            "uploaded_file": self.SAMPLE_FILE_DATA,
            "not_a_file2": "just a value2",
            "uploaded_files": [self.SAMPLE_FILE_DATA, self.SAMPLE_FILE_DATA],
            "not_a_file3": "just a value3",
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)
        ProcessInstanceService.replace_file_data_with_digest_references(data, models)

        assert data == {
            "not_a_file": "just a value",
            "uploaded_file": self.SAMPLE_DIGEST_REFERENCE,
            "not_a_file2": "just a value2",
            "uploaded_files": [
                self.SAMPLE_DIGEST_REFERENCE,
                self.SAMPLE_DIGEST_REFERENCE,
            ],
            "not_a_file3": "just a value3",
        }

    def test_can_create_file_data_models_for_mulitple_single_file_data_values(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        data = {
            "File": [
                {
                    "supporting_files": self.SAMPLE_FILE_DATA,
                },
                {
                    "supporting_files": self.SAMPLE_FILE_DATA,
                },
            ],
        }
        models = ProcessInstanceService.file_data_models_for_data(data, 111)

        assert len(models) == 2
        self._check_sample_file_data_model("File", 0, models[0])
        self._check_sample_file_data_model("File", 1, models[1])

    def test_does_not_skip_events_it_does_not_know_about(self) -> None:
        name = None
        event_type = "Unknown"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert not (
            ProcessInstanceService.waiting_event_can_be_skipped(
                pending_event,
                datetime.now(timezone.utc),
            )
        )

    def test_does_skip_duration_timer_events_for_the_future(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert ProcessInstanceService.waiting_event_can_be_skipped(
            pending_event,
            datetime.fromisoformat("2023-04-26T20:15:10.626656+00:00"),
        )

    def test_does_not_skip_duration_timer_events_for_the_past(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert not (
            ProcessInstanceService.waiting_event_can_be_skipped(
                pending_event,
                datetime.fromisoformat("2023-04-28T20:15:10.626656+00:00"),
            )
        )

    def test_does_not_skip_duration_timer_events_for_now(self) -> None:
        name = None
        event_type = "DurationTimerEventDefinition"
        value = "2023-04-27T20:15:10.626656+00:00"
        pending_event = PendingBpmnEvent(name, event_type, value)
        assert not (
            ProcessInstanceService.waiting_event_can_be_skipped(
                pending_event,
                datetime.fromisoformat("2023-04-27T20:15:10.626656+00:00"),
            )
        )

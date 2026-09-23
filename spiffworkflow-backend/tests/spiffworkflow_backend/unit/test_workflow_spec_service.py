import json
from datetime import datetime
from unittest.mock import Mock
from unittest.mock import patch

import pytest

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.model_sources import ModelSource
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.workflow_spec_service import WorkflowSpecService

SIMPLE_BPMN = (
    b'<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" targetNamespace="test">'
    b'<process id="main" isExecutable="true"><startEvent id="start"/>'
    b'<sequenceFlow id="flow" sourceRef="start" targetRef="end"/><endEvent id="end"/>'
    b'</process></definitions>'
)


@pytest.mark.parametrize("repository", [True, False], ids=["repository", "supplied-files"])
@pytest.mark.parametrize(
    ("xml", "process_id", "error_code"),
    [
        (SIMPLE_BPMN, "main", None),
        (b"<invalid", "main", "invalid_xml"),
        (SIMPLE_BPMN, None, "no_primary_bpmn_error"),
        (SIMPLE_BPMN, "missing", "process_instance_validation_error"),
    ],
)
def test_source_paths_share_compilation_and_validation(
    repository: bool, xml: bytes, process_id: str | None, error_code: str | None
) -> None:
    model = ProcessModelInfo(id="example", display_name="Example", description="", primary_process_id=process_id)
    file = File(content_type="text/xml", name="model.bpmn", type="bpmn", last_modified=datetime.now(), size=len(xml))
    contents = {
        "example/process_model.json": json.dumps({"primary_process_id": process_id}).encode(),
        "example/model.bpmn": xml,
    }
    files = Mock(spec=["paths", "read"])
    files.paths.return_value = contents.keys()
    files.read.side_effect = contents.__getitem__

    def compile_spec() -> tuple:
        if repository:
            return WorkflowSpecService.get_spec([file], model)
        return ModelSource(files=files).specs(model.id)

    with (
        patch.object(SpecFileService, "get_data", return_value=xml),
        patch.object(WorkflowSpecService, "update_spiff_parser_with_all_process_dependency_files") as dependencies,
    ):
        if error_code is None:
            spec, subprocesses = compile_spec()
            assert spec.name == "main"
            assert subprocesses == {}
        else:
            with pytest.raises(ApiError) as raised:
                compile_spec()
            assert raised.value.error_code == error_code
            if error_code == "invalid_xml":
                assert raised.value.file_name == ("model.bpmn" if repository else "example/model.bpmn")
        if repository and error_code not in ("invalid_xml", "no_primary_bpmn_error"):
            dependencies.assert_called_once()
        else:
            dependencies.assert_not_called()


def test_missing_called_process_never_uses_repository_for_supplied_files() -> None:
    xml = SIMPLE_BPMN.replace(b'<endEvent id="end"/>', b'<callActivity id="end" calledElement="other"/>')
    with patch.object(WorkflowSpecService, "bpmn_file_full_path_from_bpmn_process_identifier") as repository_lookup:
        with pytest.raises(ApiError) as raised:
            WorkflowSpecService.get_spec_from_files([("example/model.bpmn", "bpmn", xml)], "example", "main")
        assert raised.value.error_code == "process_instance_validation_error"
        repository_lookup.assert_not_called()

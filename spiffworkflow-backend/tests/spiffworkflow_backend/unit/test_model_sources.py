import json
from collections.abc import Iterable
from unittest.mock import patch

import pytest

from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.services.model_sources import ModelSource
from spiffworkflow_backend.services.model_sources import ModelSources


class MemoryFiles:
    def __init__(self, files: dict[str, bytes]):
        self.files = files

    def paths(self) -> Iterable[str]:
        return self.files.keys()

    def read(self, path: str) -> bytes:
        try:
            return self.files[path]
        except KeyError as error:
            raise FileNotFoundError(path) from error


@pytest.fixture
def source() -> ModelSource:
    config = json.dumps({"display_name": "Example", "description": "Test", "primary_process_id": "main"}).encode()
    return ModelSource(
        files=MemoryFiles(
            {
                "example/process_model.json": config,
                "example/main.bpmn": (
                    b'<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" targetNamespace="test">'
                    b'<process id="main" isExecutable="true"><startEvent id="start"/>'
                    b'<sequenceFlow id="flow" sourceRef="start" targetRef="end"/><endEvent id="end"/>'
                    b'</process></definitions>'
                ),
                "called/process_model.json": config,
                "called/model.bpmn": (
                    b'<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL">'
                    b'<process id="called"><subProcess id="embedded"/></process></definitions>'
                ),
                "example/form.json": b'{"title":"root"}',
                "called/form.json": b'{"title":"called"}',
            }
        )
    )


def test_configuration_comes_from_supplied_files(source: ModelSource) -> None:
    model = source.model("example")
    assert model.id == "example"
    assert model.display_name == "Example"


def test_specs_compile_supplied_bytes() -> None:
    config = b'{"primary_process_id":"main"}'
    xml = (
        b'<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL" targetNamespace="test">'
        b'<process id="main" isExecutable="true"><startEvent id="start"/>'
        b'<sequenceFlow id="flow" sourceRef="start" targetRef="end"/><endEvent id="end"/>'
        b'</process></definitions>'
    )
    source = ModelSource(files=MemoryFiles({"example/process_model.json": config, "example/model.bpmn": xml}))
    spec, _ = source.specs("example")
    assert spec.name == "main"


def test_forms_resolve_using_process_ownership(source: ModelSource) -> None:
    assert source.task_file("main", "form.json") == b'{"title":"root"}'
    assert source.task_file("called", "form.json") == b'{"title":"called"}'
    assert source.task_file("embedded", "form.json") == b'{"title":"called"}'


@pytest.mark.parametrize("filename", ["", ".", "..", "../form.json", "/form.json", "other/form.json", "other\\form.json"])
def test_form_paths_must_be_unqualified(source: ModelSource, filename: str) -> None:
    with pytest.raises(ValueError):
        source.task_file("main", filename)


def test_missing_supplied_file_does_not_use_repository(source: ModelSource) -> None:
    with patch("spiffworkflow_backend.services.git_service.GitService.get_file_contents_for_revision_if_git_revision") as read:
        with pytest.raises(FileNotFoundError):
            source.task_file("main", "missing.json")
        read.assert_not_called()


def test_diagram_errors_are_returned_in_payload(source: ModelSource) -> None:
    instance = ProcessInstanceModel(id=1, process_model_identifier="example")
    payload = source.diagram_payload(instance, "missing")
    assert payload["bpmn_xml_file_contents"] is None
    assert "missing" in payload["bpmn_xml_file_contents_retrieval_error"]


def test_ambiguous_process_ownership_is_rejected() -> None:
    xml = b'<definitions xmlns="http://www.omg.org/spec/BPMN/20100524/MODEL"><process id="same"/></definitions>'
    source = ModelSource(files=MemoryFiles({"first/model.bpmn": xml, "second/model.bpmn": xml}))
    with pytest.raises(FileNotFoundError, match="Ambiguous BPMN"):
        source.task_file("same", "form.json")


def test_no_provider_selects_repository() -> None:
    assert ModelSources.for_instance(ProcessInstanceModel(id=1)).files is None

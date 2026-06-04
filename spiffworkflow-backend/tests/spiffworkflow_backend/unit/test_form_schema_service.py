from types import SimpleNamespace
from typing import Any

import pytest

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.form_schema_service import FormSchemaService
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.task_service import TaskModelError


def test_prepare_form_data_adds_form_file_note_to_task_model_error(monkeypatch: pytest.MonkeyPatch) -> None:
    task_model = SimpleNamespace(data={"customer": "Ada"})

    monkeypatch.setattr(TaskModelError, "get_task_trace", classmethod(lambda cls, task_model: []))
    monkeypatch.setattr(
        GitService,
        "get_file_contents_for_revision_if_git_revision",
        lambda **kwargs: "{{ broken_form_template }}",
    )

    def raise_task_model_error(*args: Any, **kwargs: Any) -> str:
        raise TaskModelError("template failed", task_model=task_model, exception=ValueError("boom"))  # type: ignore[arg-type]

    def api_error_from_workflow_exception(error_code: str, message: str, exp: TaskModelError) -> ApiError:
        return ApiError(error_code=error_code, message=message, status_code=400)

    monkeypatch.setattr(JinjaService, "render_jinja_template", raise_task_model_error)
    monkeypatch.setattr(ApiError, "from_workflow_exception", api_error_from_workflow_exception)

    with pytest.raises(ApiError) as exception:
        FormSchemaService.prepare_form_data(
            "form.json",
            ProcessModelInfo(id="test/form-model", display_name="Test Form Model", description=""),
            task_model=task_model,  # type: ignore[arg-type]
        )

    assert exception.value.file_name == "form.json"
    assert isinstance(exception.value.__cause__, TaskModelError)
    assert "Error in Json Form File 'form.json'" in exception.value.__cause__.notes

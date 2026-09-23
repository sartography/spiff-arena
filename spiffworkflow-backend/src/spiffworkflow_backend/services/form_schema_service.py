import json

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.jinja_service import JinjaService
from spiffworkflow_backend.services.process_model_history import process_model_history
from spiffworkflow_backend.services.task_service import TaskModelError


class FormSchemaService:
    @classmethod
    def prepare_form_data(
        cls,
        form_file: str,
        process_model: ProcessModelInfo,
        task_model: TaskModel | None = None,
        revision: str | None = None,
    ) -> dict:
        try:
            history = process_model_history(task_model.process_instance_id) if task_model is not None else None
            if task_model is not None and history is not None:
                form_contents = history.task_file(
                    task_model.process_instance_id,
                    task_model.bpmn_process.bpmn_process_definition.bpmn_identifier,
                    form_file,
                ).decode("utf-8")
            else:
                form_contents = GitService.get_file_contents_for_revision_if_git_revision(
                    process_model=process_model, revision=revision, file_name=form_file
                )
        except ValueError as exception:
            raise ApiError("form_schema_invalid_reference", str(exception), status_code=400) from exception
        except FileNotFoundError as exception:
            raise ApiError("form_schema_file_unavailable", str(exception), status_code=404) from exception
        except GitCommandError as exception:
            raise ApiError(
                error_code="git_error_loading_form",
                message=(
                    f"Could not load form schema from: {form_file}. Was git history rewritten such that revision"
                    f" '{revision}' no longer exists? Error was: {str(exception)}"
                ),
                status_code=400,
            ) from exception

        if task_model and task_model.data is not None:
            try:
                form_contents = JinjaService.render_jinja_template(form_contents, task=task_model)
            except TaskModelError as wfe:
                wfe.add_note(f"Error in Json Form File '{form_file}'")
                api_error = ApiError.from_workflow_exception("instructions_error", str(wfe), exp=wfe)
                api_error.file_name = form_file
                raise api_error from wfe

        try:
            hot_dict: dict = json.loads(form_contents)
            return hot_dict
        except Exception as exception:
            raise ApiError(
                error_code="error_loading_form",
                message=f"Could not load form schema from: {form_file}. Error was: {str(exception)}",
                status_code=400,
            ) from exception

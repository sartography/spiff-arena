from flask import g

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.services.process_model_import_service import ProcessModelImportService


def process_model_import(modified_process_group_id: str, body: dict) -> tuple[dict, int]:
    repository_url = body.get("repository_url")
    if not repository_url:
        raise ApiError("missing_repository_url", "Repository URL is required", status_code=400)

    if not ProcessModelImportService.is_valid_github_url(repository_url):
        raise ApiError("invalid_github_url", "The provided URL is not a valid GitHub repository URL", status_code=400)

    unmodified_process_group_id = modified_process_group_id.replace(":", "/")
    process_model = ProcessModelImportService.import_from_github_url(
        url=repository_url, process_group_id=unmodified_process_group_id
    )
    _commit_and_push_to_git(
        f"User: {g.user.username} imported process model from {repository_url} into {unmodified_process_group_id}"
    )

    return {"process_model": process_model.to_dict(), "import_source": repository_url}, 201

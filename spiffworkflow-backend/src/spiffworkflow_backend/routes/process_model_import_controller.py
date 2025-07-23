"""APIs for importing process models from external sources."""

from flask import request

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.process_model_import_service import GitHubRepositoryNotFoundError
from spiffworkflow_backend.services.process_model_import_service import InvalidProcessModelError
from spiffworkflow_backend.services.process_model_import_service import ProcessGroupNotFoundError
from spiffworkflow_backend.services.process_model_import_service import ProcessModelImportService
from spiffworkflow_backend.services.process_model_import_service import is_valid_github_url


def process_model_import(modified_process_group_id: str) -> tuple[dict, int]:
    """Import a process model from a GitHub URL."""

    # Get request data
    body = request.json
    if not body:
        raise ApiError("missing_request_body", "Request body is required", status_code=400)

    repository_url = body.get("repository_url")
    if not repository_url:
        raise ApiError("missing_repository_url", "Repository URL is required", status_code=400)

    # Validate the URL
    if not is_valid_github_url(repository_url):
        raise ApiError("invalid_github_url", "The provided URL is not a valid GitHub repository URL", status_code=400)

    # Unmodify process group ID (replace : with /)
    unmodified_process_group_id = modified_process_group_id.replace(":", "/")

    # Process the import
    try:
        process_model = ProcessModelImportService.import_from_github_url(
            url=repository_url, process_group_id=unmodified_process_group_id
        )

        # Return the imported process model
        return {"process_model": process_model.to_dict(), "import_source": repository_url}, 201

    except ProcessGroupNotFoundError as ex:
        raise ApiError(
            "process_group_not_found", f"The specified process group was not found: {str(ex)}", status_code=404
        ) from ex
    except GitHubRepositoryNotFoundError as ex:
        raise ApiError(
            "github_repository_not_found", f"The specified GitHub repository was not found: {str(ex)}", status_code=404
        ) from ex
    except InvalidProcessModelError as ex:
        raise ApiError(
            "invalid_process_model", f"The repository does not contain a valid process model: {str(ex)}", status_code=400
        ) from ex

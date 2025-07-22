"""APIs for importing process models from external sources."""

from flask import request

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.process_api_blueprint import process_api_blueprint
from spiffworkflow_backend.services.process_model_import_service import GitHubRepositoryNotFoundError
from spiffworkflow_backend.services.process_model_import_service import InvalidProcessModelError
from spiffworkflow_backend.services.process_model_import_service import ProcessGroupNotFoundError
from spiffworkflow_backend.services.process_model_import_service import ProcessModelImportService
from spiffworkflow_backend.services.process_model_import_service import is_valid_github_url


# Function will be mapped to POST /process-models/{process_group_id}/import in the OpenAPI spec
@process_api_blueprint.route("/process-models/<process_group_id>/import", methods=["POST"])
def process_model_import(process_group_id):
    """Import a process model from a GitHub URL."""

    # Get request data
    body = request.json
    repository_url = body.get("repository_url")

    # Validate the URL
    if not repository_url or not is_valid_github_url(repository_url):
        raise ApiError("invalid_github_url", "The provided URL is not a valid GitHub repository URL", status_code=400)

    # Process the import
    try:
        process_model = ProcessModelImportService.import_from_github_url(repository_url, process_group_id)

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

from flask import g

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.services.process_model_import_service import ModelAliasNotFoundError
from spiffworkflow_backend.services.process_model_import_service import ModelMarketplaceError
from spiffworkflow_backend.services.process_model_import_service import ProcessModelImportService


def process_model_import(modified_process_group_id: str, body: dict) -> tuple[dict, int]:
    repository_url = body.get("repository_url")
    if not repository_url:
        raise ApiError("missing_repository_url", "Repository URL or model alias is required", status_code=400)

    unmodified_process_group_id = modified_process_group_id.replace(":", "/")

    # Determine if it's a GitHub URL or a model alias
    import_source_type = "github"
    if ProcessModelImportService.is_valid_github_url(repository_url):
        try:
            process_model = ProcessModelImportService.import_from_github_url(
                url=repository_url, process_group_id=unmodified_process_group_id
            )
        except Exception as ex:
            raise ApiError("github_import_error", str(ex), status_code=500)
    elif ProcessModelImportService.is_model_alias(repository_url):
        try:
            process_model = ProcessModelImportService.import_from_model_alias(
                alias=repository_url, process_group_id=unmodified_process_group_id
            )
            import_source_type = "marketplace"
        except ModelAliasNotFoundError as ex:
            raise ApiError("model_alias_not_found", str(ex), status_code=404)
        except ModelMarketplaceError as ex:
            raise ApiError("marketplace_error", str(ex), status_code=500)
    else:
        raise ApiError("invalid_import_source", "The provided value is not a valid GitHub URL or model alias", status_code=400)

    _commit_and_push_to_git(
        f"User: {g.user.username} imported process model from {import_source_type} ({repository_url}) into {unmodified_process_group_id}"
    )

    return {"process_model": process_model.to_dict(), "import_source": repository_url}, 201

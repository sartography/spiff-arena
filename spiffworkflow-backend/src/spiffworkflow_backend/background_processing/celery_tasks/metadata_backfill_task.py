from typing import Any
from typing import cast

from celery import shared_task
from flask import current_app

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.services.metadata_backfill_service import MetadataBackfillService

# Ten minutes timeout for the task
ten_minutes = 60 * 10


def _celery_task_backfill_metadata_impl(
    celery_task_id: str, process_model_identifier: str, metadata_paths: list[dict[str, str]]
) -> dict[str, Any]:
    logger_prefix = f"celery_task_backfill_metadata[{celery_task_id}]"
    current_app.logger.info(f"{logger_prefix}: Starting metadata backfill for process model: {process_model_identifier}")

    try:
        results = MetadataBackfillService.backfill_metadata_for_model(process_model_identifier, metadata_paths)
        current_app.logger.info(
            f"{logger_prefix}: Completed metadata backfill for process model: {process_model_identifier}. "
            f"Processed: {results.get('instances_processed', 0)}, "
            f"Updated: {results.get('instances_updated', 0)}, "
            f"Time: {results.get('execution_time', 0):.2f}s"
        )

        return {
            "ok": True,
            "process_model_identifier": process_model_identifier,
            "statistics": results,
        }
    except Exception as exception:
        db.session.rollback()
        error_message = (
            f"{logger_prefix}: Error running metadata backfill for process model {process_model_identifier}. {str(exception)}"
        )
        current_app.logger.error(error_message)
        return {
            "ok": False,
            "process_model_identifier": process_model_identifier,
            "error": str(exception),
        }


@shared_task(ignore_result=False, time_limit=ten_minutes, bind=True)
def celery_task_backfill_metadata(
    self: Any, process_model_identifier: str, metadata_paths: list[dict[str, str]]
) -> dict[str, Any]:
    celery_task_id = self.request.id
    return _celery_task_backfill_metadata_impl(celery_task_id, process_model_identifier, metadata_paths)


def trigger_metadata_backfill(
    process_model_identifier: str,
    old_metadata_extraction_paths: list[dict[str, str]] | None = None,
    new_metadata_extraction_paths: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    if not current_app.config.get("SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED", False):
        return {"status": "skipped", "reason": "Metadata backfill feature is disabled"}

    new_metadata_paths = MetadataBackfillService.detect_metadata_changes(
        old_metadata_extraction_paths, new_metadata_extraction_paths
    )

    if not new_metadata_paths:
        return {"status": "skipped", "reason": "No new metadata paths detected"}

    task = cast(Any, celery_task_backfill_metadata).delay(process_model_identifier, new_metadata_paths)

    current_app.logger.info(
        f"Triggered metadata backfill for process model {process_model_identifier} with task ID: {task.id}. "
        f"New metadata paths: {[path['key'] for path in new_metadata_paths]}"
    )

    return {
        "status": "triggered",
        "task_id": task.id,
        "process_model_id": process_model_identifier,
        "new_metadata_paths": [path["key"] for path in new_metadata_paths],
    }

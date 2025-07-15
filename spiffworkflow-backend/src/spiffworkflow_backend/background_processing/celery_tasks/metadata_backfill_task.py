"""Celery task for backfilling process instance metadata."""
from typing import Any, cast

from celery import shared_task
from flask import current_app

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.metadata_backfill_service import MetadataBackfillService
from spiffworkflow_backend.services.process_model_service import ProcessModelService

# Ten minutes timeout for the task
ten_minutes = 60 * 10


def _celery_task_backfill_metadata_impl(
    celery_task_id: str, process_model_identifier: str, metadata_paths: list[dict[str, str]]
) -> dict[str, Any]:
    """Implementation of the metadata backfill task.
    
    Args:
        celery_task_id: The ID of the Celery task
        process_model_identifier: The identifier of the process model
        metadata_paths: List of new metadata extraction paths to apply
        
    Returns:
        Statistics about the backfill operation
    """
    logger_prefix = f"celery_task_backfill_metadata[{celery_task_id}]"
    
    current_app.logger.info(
        f"{logger_prefix}: Starting metadata backfill for process model: {process_model_identifier}"
    )
    
    try:
        # Run the backfill operation
        results = MetadataBackfillService.backfill_metadata_for_model(
            process_model_identifier, metadata_paths
        )
        
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
        db.session.rollback()  # In case the above left the database with a bad transaction
        error_message = (
            f"{logger_prefix}: Error running metadata backfill for "
            f"process model {process_model_identifier}. {str(exception)}"
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
    """Execute metadata backfill as a background task.

    Args:
        self: The bound Celery task object
        process_model_identifier: The identifier of the process model
        metadata_paths: List of new metadata extraction paths to apply

    Returns:
        Statistics about the backfill operation
    """
    celery_task_id = self.request.id
    return _celery_task_backfill_metadata_impl(celery_task_id, process_model_identifier, metadata_paths)


def trigger_metadata_backfill(old_model: ProcessModelInfo, new_model: ProcessModelInfo) -> dict[str, Any]:
    """Detect metadata changes and trigger backfill if needed.
    
    Args:
        old_model: The previous version of the process model
        new_model: The updated version of the process model
        
    Returns:
        Information about the triggered task or a message if no backfill was needed
    """
    # Check if the feature is enabled in the configuration
    if not current_app.config.get("SPIFFWORKFLOW_BACKEND_PROCESS_INSTANCE_METADATA_BACKFILL_ENABLED", False):
        return {"status": "skipped", "reason": "Metadata backfill feature is disabled"}
    
    # Detect new metadata extraction paths
    new_metadata_paths = MetadataBackfillService.detect_metadata_changes(old_model, new_model)
    
    # If there are no new metadata paths, no need to trigger backfill
    if not new_metadata_paths:
        return {"status": "skipped", "reason": "No new metadata paths detected"}
    
    # Trigger the Celery task
    task = cast(Any, celery_task_backfill_metadata).delay(new_model.id, new_metadata_paths)
    
    current_app.logger.info(
        f"Triggered metadata backfill for process model {new_model.id} with task ID: {task.id}. "
        f"New metadata paths: {[path['key'] for path in new_metadata_paths]}"
    )
    
    return {
        "status": "triggered",
        "task_id": task.id,
        "process_model_id": new_model.id,
        "new_metadata_paths": [path["key"] for path in new_metadata_paths],
    }
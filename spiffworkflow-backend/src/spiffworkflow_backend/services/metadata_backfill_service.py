"""Service to handle backfilling of process instance metadata.

When a process model adds new metadata extraction paths, this service handles
backfilling the metadata for existing process instances.
"""

import time
from typing import Any

from flask import current_app
from sqlalchemy import desc

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_instance_metadata import ProcessInstanceMetadataModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.task import TaskModel


class MetadataBackfillService:
    """Service for backfilling process instance metadata when metadata extraction paths are added."""

    BATCH_SIZE = 100  # Number of process instances to process in a single batch

    @classmethod
    def detect_metadata_changes(cls, old_model: ProcessModelInfo, new_model: ProcessModelInfo) -> list[dict[str, str]]:
        """Detect new metadata extraction paths between old and new process models.

        Args:
            old_model: The previous version of the process model
            new_model: The updated version of the process model

        Returns:
            List of new metadata extraction path objects
        """
        if old_model.metadata_extraction_paths is None:
            old_paths = []
        else:
            old_paths = old_model.metadata_extraction_paths

        if new_model.metadata_extraction_paths is None:
            new_paths = []
        else:
            new_paths = new_model.metadata_extraction_paths

        # Extract just the keys for comparison
        old_keys = {path["key"] for path in old_paths}
        new_keys = {path["key"] for path in new_paths}

        # Find keys that are in new_paths but not in old_paths
        new_metadata_keys = new_keys - old_keys

        # Return the full path objects for new keys
        return [path for path in new_paths if path["key"] in new_metadata_keys]

    @classmethod
    def get_process_instances(
        cls, process_model_identifier: str, batch_size: int | None = None, offset: int = 0
    ) -> list[ProcessInstanceModel]:
        """Get process instances for a specific process model in batches.

        Args:
            process_model_identifier: The identifier of the process model
            batch_size: The number of instances to retrieve (defaults to cls.BATCH_SIZE)
            offset: The offset for pagination

        Returns:
            List of process instances
        """
        size = cls.BATCH_SIZE if batch_size is None else batch_size

        instances: list[ProcessInstanceModel] = (
            ProcessInstanceModel.query.filter_by(process_model_identifier=process_model_identifier)
            .order_by(ProcessInstanceModel.id)
            .limit(size)
            .offset(offset)
            .all()
        )
        return instances

    @classmethod
    def get_process_instance_count(cls, process_model_identifier: str) -> int:
        """Get the total count of process instances for a process model.

        Args:
            process_model_identifier: The identifier of the process model

        Returns:
            The count of process instances
        """
        count: int = ProcessInstanceModel.query.filter_by(process_model_identifier=process_model_identifier).count()
        return count

    @classmethod
    def get_latest_task_data(cls, process_instance_id: int) -> dict[str, Any]:
        """Get the data from the most recent completed task for a process instance.

        Args:
            process_instance_id: The ID of the process instance

        Returns:
            The task data as a dictionary
        """
        # SQLAlchemy's desc() works on the column itself, not the value
        latest_task = (
            TaskModel.query.filter_by(process_instance_id=process_instance_id, state="COMPLETED")
            .order_by(desc(TaskModel.end_in_seconds))  # type: ignore
            .first()
        )

        if latest_task:
            data: dict[str, Any] = latest_task.json_data()
            return data
        return {}

    @classmethod
    def extract_metadata_for_instance(
        cls, process_model_identifier: str, task_data: dict[str, Any], metadata_paths: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Extract metadata values from task data based on extraction paths.

        Args:
            process_model_identifier: The identifier of the process model
            task_data: The data from a task
            metadata_paths: The metadata extraction path configurations

        Returns:
            Dictionary mapping metadata keys to their extracted values
        """
        metadata: dict[str, Any] = {}
        for metadata_path in metadata_paths:
            key = metadata_path["key"]
            path = metadata_path["path"]
            path_segments = path.split(".")
            data_for_key: Any = task_data
            for path_segment in path_segments:
                if isinstance(data_for_key, dict) and path_segment in data_for_key:
                    data_for_key = data_for_key[path_segment]
                else:
                    data_for_key = None
                    break
            metadata[key] = data_for_key
        return metadata

    @classmethod
    def add_metadata_to_instance(cls, process_instance_id: int, metadata: dict[str, Any]) -> None:
        """Add metadata to a process instance.

        Args:
            process_instance_id: The ID of the process instance
            metadata: Dictionary of metadata key-value pairs to add
        """
        current_time = int(time.time())
        for key, value in metadata.items():
            if value is not None:
                # Check if metadata already exists
                existing_metadata = ProcessInstanceMetadataModel.query.filter_by(
                    process_instance_id=process_instance_id, key=key
                ).first()

                if existing_metadata is None:
                    # Create new metadata entry
                    new_metadata = ProcessInstanceMetadataModel(
                        process_instance_id=process_instance_id,
                        key=key,
                        value=cls.truncate_string(str(value), 255),
                        created_at_in_seconds=current_time,
                        updated_at_in_seconds=current_time,
                    )
                    db.session.add(new_metadata)

    @staticmethod
    def truncate_string(value: str, max_length: int) -> str:
        """Truncate a string to a maximum length.

        Args:
            value: The string to truncate
            max_length: The maximum allowed length

        Returns:
            The truncated string
        """
        if len(value) <= max_length:
            return value
        return value[:max_length]

    @classmethod
    def backfill_metadata_for_model(
        cls, process_model_identifier: str, new_metadata_paths: list[dict[str, str]]
    ) -> dict[str, Any]:
        """Backfill metadata for all process instances of a specific model.

        Args:
            process_model_identifier: The identifier of the process model
            new_metadata_paths: List of new metadata extraction paths to apply

        Returns:
            Statistics about the backfill operation
        """
        if not new_metadata_paths:
            return {"instances_processed": 0, "instances_updated": 0, "message": "No new metadata paths to process"}

        stats: dict[str, Any] = {"instances_processed": 0, "instances_updated": 0, "start_time": time.time()}
        total_instances = cls.get_process_instance_count(process_model_identifier)

        if total_instances == 0:
            stats["message"] = "No process instances found for this model"
            return stats

        offset = 0
        while True:
            # Get a batch of process instances
            instances = cls.get_process_instances(process_model_identifier, cls.BATCH_SIZE, offset)
            if not instances:
                break  # No more instances to process

            # Process each instance in the batch
            for instance in instances:
                try:
                    # Get the latest task data
                    task_data = cls.get_latest_task_data(instance.id)

                    # Extract metadata values from task data
                    new_metadata = cls.extract_metadata_for_instance(process_model_identifier, task_data, new_metadata_paths)

                    # Add metadata to process instance
                    if new_metadata:
                        cls.add_metadata_to_instance(instance.id, new_metadata)
                        stats["instances_updated"] += 1

                    stats["instances_processed"] += 1

                except Exception as ex:
                    current_app.logger.error(f"Error processing metadata backfill for instance {instance.id}: {str(ex)}")

            # Commit the transaction for this batch
            db.session.commit()

            # Move to next batch
            offset += cls.BATCH_SIZE

            # Log progress
            current_app.logger.info(
                f"Metadata backfill progress: {stats['instances_processed']}/{total_instances} "
                f"instances processed for model {process_model_identifier}"
            )

        # Calculate execution time and add it to stats
        stats["execution_time"] = time.time() - stats["start_time"]
        stats["message"] = (
            f"Successfully processed {stats['instances_processed']} instances, updated {stats['instances_updated']}"
        )

        return stats

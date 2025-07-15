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
    PROCESS_INSTANCE_BATCH_SIZE = 100

    @classmethod
    def detect_metadata_changes(
        cls,
        old_metadata_extraction_paths: list[dict[str, str]] | None = None,
        new_metadata_extraction_paths: list[dict[str, str]] | None = None,
    ) -> list[dict[str, str]]:
        old_paths = old_metadata_extraction_paths or []
        new_paths = new_metadata_extraction_paths or []

        old_keys = {path["key"] for path in old_paths}
        new_keys = {path["key"] for path in new_paths}

        new_metadata_keys = new_keys - old_keys

        return [path for path in new_paths if path["key"] in new_metadata_keys]

    @classmethod
    def get_process_instances(
        cls, process_model_identifier: str, batch_size: int | None = None, offset: int = 0
    ) -> list[ProcessInstanceModel]:
        size = cls.PROCESS_INSTANCE_BATCH_SIZE if batch_size is None else batch_size

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
        count: int = ProcessInstanceModel.query.filter_by(process_model_identifier=process_model_identifier).count()
        return count

    @classmethod
    def get_latest_task_data(cls, process_instance_id: int) -> dict[str, Any]:
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
    def add_metadata_to_instance(cls, process_instance_id: int, metadata: dict[str, Any]) -> None:
        for key, value in metadata.items():
            if value is not None:
                existing_metadata = ProcessInstanceMetadataModel.query.filter_by(
                    process_instance_id=process_instance_id, key=key
                ).first()

                if existing_metadata is None:
                    new_metadata = ProcessInstanceMetadataModel(
                        process_instance_id=process_instance_id,
                        key=key,
                        value=cls.truncate_string(str(value), 255),
                    )
                    db.session.add(new_metadata)

    @staticmethod
    def truncate_string(value: str, max_length: int) -> str:
        if len(value) <= max_length:
            return value
        return value[:max_length]

    @classmethod
    def backfill_metadata_for_model(
        cls, process_model_identifier: str, new_metadata_paths: list[dict[str, str]]
    ) -> dict[str, Any]:
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
            instances = cls.get_process_instances(process_model_identifier, cls.PROCESS_INSTANCE_BATCH_SIZE, offset=offset)
            if not instances:
                break

            for instance in instances:
                try:
                    task_data = cls.get_latest_task_data(instance.id)
                    new_metadata = ProcessModelInfo.extract_metadata(task_data, new_metadata_paths)
                    if new_metadata:
                        cls.add_metadata_to_instance(instance.id, new_metadata)
                        stats["instances_updated"] += 1

                    stats["instances_processed"] += 1

                except Exception as ex:
                    current_app.logger.error(f"Error processing metadata backfill for instance {instance.id}: {str(ex)}")

            db.session.commit()
            offset += cls.PROCESS_INSTANCE_BATCH_SIZE

            current_app.logger.info(
                f"Metadata backfill progress: {stats['instances_processed']}/{total_instances} "
                f"instances processed for model {process_model_identifier}"
            )

        stats["execution_time"] = time.time() - stats["start_time"]
        stats["message"] = (
            f"Successfully processed {stats['instances_processed']} instances, updated {stats['instances_updated']}"
        )

        return stats

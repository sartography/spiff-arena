import os

from flask import current_app
from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.reference_cache_service import ReferenceCacheService
from sqlalchemy import insert


class DataSetupService:
    @classmethod
    def run_setup(cls) -> list:
        return cls.save_all_process_models()

    @classmethod
    def add_unique_reference_cache_object(
        cls, reference_objects: dict[str, ReferenceCacheModel], reference_cache: ReferenceCacheModel
    ) -> None:
        reference_cache_unique = (
            f"{reference_cache.identifier}{reference_cache.relative_location}{reference_cache.type}"
        )
        reference_objects[reference_cache_unique] = reference_cache

    @classmethod
    def save_all_process_models(cls) -> list:
        """Build a cache of all processes, messages, correlation keys, and start events.

        These all exist within processes located on the file system, so we can quickly reference them
        from the database.
        """
        current_app.logger.debug("DataSetupService.save_all_process_models() start")

        failing_process_models = []
        files = FileSystemService.walk_files_from_root_path(True, None)
        reference_objects: dict[str, ReferenceCacheModel] = {}
        for file in files:
            if FileSystemService.is_process_model_json_file(file):
                process_model = ProcessModelService.get_process_model_from_path(file)
                current_app.logger.debug(f"Process Model: {process_model.display_name}")
                try:
                    # FIXME: get_references_for_file_contents is erroring out for elements in the list
                    refs = SpecFileService.get_references_for_process(process_model)

                    for ref in refs:
                        try:
                            reference_cache = ReferenceCacheModel.from_spec_reference(ref)
                            cls.add_unique_reference_cache_object(reference_objects, reference_cache)
                            SpecFileService.update_caches_except_process(ref)
                            db.session.commit()
                        except Exception as ex:
                            failing_process_models.append(
                                (
                                    f"{ref.relative_location}/{ref.file_name}",
                                    str(ex),
                                )
                            )
                except Exception as ex2:
                    failing_process_models.append(
                        (
                            f"{process_model.id}",
                            str(ex2),
                        )
                    )
            elif FileSystemService.is_data_store_json_file(file):
                relative_location = FileSystemService.relative_location(file)
                file_name = os.path.basename(file)
                (identifier, _) = os.path.splitext(file_name)
                reference_cache = ReferenceCacheModel.from_params(
                    identifier,
                    identifier,
                    "data_store",
                    file_name,
                    relative_location,
                    None,
                    False,
                )
                cls.add_unique_reference_cache_object(reference_objects, reference_cache)

        current_app.logger.debug("DataSetupService.save_all_process_models() end")

        ReferenceCacheService.add_new_generation(reference_objects)
        
        return failing_process_models

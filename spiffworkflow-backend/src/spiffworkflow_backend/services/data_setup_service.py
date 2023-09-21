from flask import current_app
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


class DataSetupService:
    @classmethod
    def run_setup(cls) -> list:
        return cls.save_all_process_models()

    @classmethod
    def save_all_process_models(cls) -> list:
        """Build a cache of all processes, messages, correlation keys, and start events.

        These all exist within processes located on the file system, so we can quickly reference them
        from the database.
        """
        current_app.logger.debug("DataSetupService.save_all_process_models() start")
        failing_process_models = []
        process_models = ProcessModelService.get_process_models(recursive=True)
        cache_generation = CacheGenerationModel(cache_table="reference_cache")
        reference_objects = {}
        for process_model in process_models:
            current_app.logger.debug(f"Process Model: {process_model.display_name}")
            try:
                refs = SpecFileService.get_references_for_process(process_model)
                for ref in refs:
                    try:
                        reference_cache = ReferenceCacheModel.from_spec_reference(ref, cache_generation=cache_generation)
                        reference_cache_unique = f"{reference_cache.identifier}{reference_cache.relative_location}{reference_cache.type}"
                        reference_objects[reference_cache_unique] = reference_cache
                        SpecFileService.update_caches(ref)
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

        current_app.logger.debug("DataSetupService.save_all_process_models() end")
        db.session.add(cache_generation)
        db.session.add_all(reference_objects.values())
        db.session.commit()
        return failing_process_models

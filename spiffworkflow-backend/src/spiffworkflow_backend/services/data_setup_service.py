from flask import current_app
from spiffworkflow_backend.models.cache_generation import CacheGenerationModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from sqlalchemy import insert


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

        # tmp
        # for file in FileSystemService.walk_files_from_root_path():
        #    current_app.logger.info(f"FILE: {file}")
        # exit(1)

        failing_process_models = []
        process_models = ProcessModelService.get_process_models(recursive=True)
        reference_objects = {}
        for process_model in process_models:
            current_app.logger.debug(f"Process Model: {process_model.display_name}")
            try:
                # FIXME: get_references_for_file_contents is erroring out for elements in the list
                refs = SpecFileService.get_references_for_process(process_model)

                for ref in refs:
                    try:
                        reference_cache = ReferenceCacheModel.from_spec_reference(ref)
                        reference_cache_unique = (
                            f"{reference_cache.identifier}{reference_cache.relative_location}{reference_cache.type}"
                        )
                        reference_objects[reference_cache_unique] = reference_cache
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

        current_app.logger.debug("DataSetupService.save_all_process_models() end")

        # get inserted autoincrement primary key value back in a database agnostic way without committing the db session
        ins = insert(CacheGenerationModel).values(cache_table="reference_cache")  # type: ignore
        res = db.session.execute(ins)
        cache_generation_id = res.inserted_primary_key[0]

        # add primary key value to each element in reference objects list and store in new list
        reference_object_list_with_cache_generation_id = []
        for reference_object in reference_objects.values():
            reference_object.generation_id = cache_generation_id
            reference_object_list_with_cache_generation_id.append(reference_object)

        db.session.bulk_save_objects(reference_object_list_with_cache_generation_id)
        db.session.commit()
        return failing_process_models

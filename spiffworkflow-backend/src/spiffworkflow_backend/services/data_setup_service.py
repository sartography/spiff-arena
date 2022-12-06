"""Data_setup_service."""
from flask_bpmn.models.db import db

from flask import current_app

from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


class DataSetupService:
    """DataSetupService."""

    @classmethod
    def run_setup(cls) -> list:
        """Run_setup."""
        return cls.save_all_process_models()

    @classmethod
    def save_all_process_models(cls) -> list:
        """Build a cache of all processes, messages, correlation keys, and start events.

        These all exist within processes located on the file system, so we can quickly reference them
        from the database.
        """
        # Clear out all of the cached data.
        SpecFileService.clear_caches()

        current_app.logger.debug("DataSetupService.save_all_process_models() start")
        failing_process_models = []
        process_models = ProcessModelService.get_process_models(recursive=True)
        SpecFileService.clear_caches()
        for process_model in process_models:
            current_app.logger.debug(f"Process Model: {process_model.display_name}")
            try:
                refs = SpecFileService.get_references_for_process(process_model)
                for ref in refs:
                    try:
                        SpecFileService.update_caches(ref)
                    except Exception as ex:
                        failing_process_models.append(
                            (
                                f"{ref.process_model_id}/{ref.file_name}",
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

                current_app.logger.debug(
                    "DataSetupService.save_all_process_models() end"
                )
        db.session.commit()
        return failing_process_models

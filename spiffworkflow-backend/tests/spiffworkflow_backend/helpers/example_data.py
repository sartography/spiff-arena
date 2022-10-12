"""Example_data."""
import glob
import os
from typing import Optional

from flask import current_app

from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


class ExampleDataLoader:
    """ExampleDataLoader."""

    def create_spec(
        self,
        process_model_id: str,
        display_name: str = "",
        description: str = "",
        master_spec: bool = False,
        process_group_id: str = "",
        display_order: int = 0,
        from_tests: bool = False,
        standalone: bool = False,
        library: bool = False,
        bpmn_file_name: Optional[str] = None,
        process_model_source_directory: Optional[str] = None,
    ) -> ProcessModelInfo:
        """Assumes that a directory exists in static/bpmn with the same name as the given process_model_id.

        further assumes that the [process_model_id].bpmn is the primary file for the process model.
        returns an array of data models to be added to the database.
        """
        spec = ProcessModelInfo(
            id=process_model_id,
            display_name=display_name,
            description=description,
            process_group_id=process_group_id,
            display_order=display_order,
            is_master_spec=master_spec,
            standalone=standalone,
            library=library,
            is_review=False,
            libraries=[],
        )
        workflow_spec_service = ProcessModelService()
        workflow_spec_service.add_spec(spec)

        bpmn_file_name_with_extension = bpmn_file_name
        if not bpmn_file_name_with_extension:
            bpmn_file_name_with_extension = process_model_id

        if not bpmn_file_name_with_extension.endswith(".bpmn"):
            bpmn_file_name_with_extension += ".bpmn"

        process_model_source_directory_to_use = process_model_source_directory
        if not process_model_source_directory_to_use:
            process_model_source_directory_to_use = process_model_id

        file_name_matcher = "*.*"
        if bpmn_file_name:
            file_name_matcher = bpmn_file_name_with_extension

        file_glob = ""
        if from_tests:
            file_glob = os.path.join(
                current_app.instance_path,
                "..",
                "..",
                "tests",
                "data",
                process_model_source_directory_to_use,
                file_name_matcher,
            )
        else:
            file_glob = os.path.join(
                current_app.root_path,
                "static",
                "bpmn",
                process_model_source_directory_to_use,
                file_name_matcher,
            )

        files = glob.glob(file_glob)
        for file_path in files:
            if os.path.isdir(file_path):
                continue  # Don't try to process sub directories

            filename = os.path.basename(file_path)
            # since there are multiple bpmn files in a test data directory, ensure we set the correct one as the primary
            is_primary = filename.lower() == bpmn_file_name_with_extension
            file = None
            try:
                file = open(file_path, "rb")
                data = file.read()
                SpecFileService.add_file(
                    process_model_info=spec, file_name=filename, binary_data=data
                )
                if is_primary:
                    SpecFileService.process_bpmn_file(
                        spec, filename, data, set_primary_file=True
                    )
                    workflow_spec_service = ProcessModelService()
                    workflow_spec_service.save_process_model(spec)
            finally:
                if file:
                    file.close()
        return spec

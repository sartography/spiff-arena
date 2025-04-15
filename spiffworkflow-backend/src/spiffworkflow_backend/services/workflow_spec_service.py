import os
from typing import NewType

from flask import current_app
from lxml import etree  # type: ignore
from lxml.etree import XMLSyntaxError  # type: ignore
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore
from SpiffWorkflow.spiff.parser.process import SpiffBpmnParser  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService

IdToBpmnProcessSpecMapping = NewType("IdToBpmnProcessSpecMapping", dict[str, BpmnProcessSpec])


class WorkflowSpecService:
    @classmethod
    def get_spec(
        cls,
        files: list[File],
        process_model_info: ProcessModelInfo,
        process_id_to_run: str | None = None,
    ) -> tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
        """Returns a SpiffWorkflow specification for the given process_instance spec, using the files provided."""
        parser = MyCustomParser()

        process_id = process_id_to_run or process_model_info.primary_process_id

        for file in files:
            data = SpecFileService.get_data(process_model_info, file.name)
            try:
                if file.type == FileType.bpmn.value:
                    bpmn: etree.Element = SpecFileService.get_etree_from_xml_bytes(data)
                    parser.add_bpmn_xml(bpmn, filename=file.name)
                elif file.type == FileType.dmn.value:
                    dmn: etree.Element = SpecFileService.get_etree_from_xml_bytes(data)
                    parser.add_dmn_xml(dmn, filename=file.name)
            except XMLSyntaxError as xse:
                raise ApiError(
                    error_code="invalid_xml",
                    message=f"'{file.name}' is not a valid xml file." + str(xse),
                ) from xse
        if process_id is None or process_id == "":
            raise (
                ApiError(
                    error_code="no_primary_bpmn_error",
                    message=f"There is no primary BPMN process id defined for process_model {process_model_info.id}",
                )
            )
        cls.update_spiff_parser_with_all_process_dependency_files(parser)

        try:
            bpmn_process_spec = parser.get_spec(process_id)

            # returns a dict of {process_id: bpmn_process_spec}, otherwise known as an IdToBpmnProcessSpecMapping
            subprocesses = parser.get_subprocess_specs(process_id)
        except ValidationException as ve:
            raise ApiError(
                error_code="process_instance_validation_error",
                message="Failed to parse the Workflow Specification. " + f"Error is '{str(ve)}.'",
                file_name=ve.file_name,
                task_name=ve.name,
                task_id=ve.id,
                tag=ve.tag,
            ) from ve
        return (bpmn_process_spec, subprocesses)

    @classmethod
    def update_spiff_parser_with_all_process_dependency_files(
        cls,
        parser: SpiffBpmnParser,
        processed_identifiers: set[str] | None = None,
    ) -> None:
        if processed_identifiers is None:
            processed_identifiers = set()
        processor_dependencies = parser.get_process_dependencies()

        # since get_process_dependencies() returns a set with None sometimes, we need to remove it
        processor_dependencies = processor_dependencies - {None}

        processor_dependencies_new = processor_dependencies - processed_identifiers
        bpmn_process_identifiers_in_parser = parser.get_process_ids()

        new_bpmn_files = set()
        for bpmn_process_identifier in processor_dependencies_new:
            # ignore identifiers that spiff already knows about
            if bpmn_process_identifier in bpmn_process_identifiers_in_parser:
                continue

            new_bpmn_file_full_path = cls.bpmn_file_full_path_from_bpmn_process_identifier(bpmn_process_identifier)
            new_bpmn_files.add(new_bpmn_file_full_path)
            dmn_file_glob = os.path.join(os.path.dirname(new_bpmn_file_full_path), "*.dmn")
            parser.add_dmn_files_by_glob(dmn_file_glob)
            processed_identifiers.add(bpmn_process_identifier)

        if new_bpmn_files:
            parser.add_bpmn_files(new_bpmn_files)
            cls.update_spiff_parser_with_all_process_dependency_files(parser, processed_identifiers)

    @classmethod
    def bpmn_file_full_path_from_bpmn_process_identifier(
        cls,
        bpmn_process_identifier: str,
    ) -> str:
        if bpmn_process_identifier is None:
            raise ValueError("bpmn_file_full_path_from_bpmn_process_identifier: bpmn_process_identifier is unexpectedly None")

        spec_reference = ReferenceCacheModel.basic_query().filter_by(identifier=bpmn_process_identifier, type="process").first()
        bpmn_file_full_path = None
        if spec_reference is None:
            bpmn_file_full_path = cls.backfill_missing_spec_reference_records(bpmn_process_identifier)
        else:
            bpmn_file_full_path = os.path.join(
                FileSystemService.root_path(),
                spec_reference.relative_path(),
            )
        if bpmn_file_full_path is None:
            raise (
                ApiError(
                    error_code="could_not_find_bpmn_process_identifier",
                    message=f"Could not find the the given bpmn process identifier from any sources: {bpmn_process_identifier}",
                )
            )
        return os.path.abspath(bpmn_file_full_path)

    @staticmethod
    def backfill_missing_spec_reference_records(
        bpmn_process_identifier: str,
    ) -> str | None:
        process_models = ProcessModelService.get_process_models(recursive=True)
        for process_model in process_models:
            try:
                refs = SpecFileService.reference_map(SpecFileService.get_references_for_process(process_model))
                bpmn_process_identifiers = refs.keys()
                if bpmn_process_identifier in bpmn_process_identifiers:
                    SpecFileService.update_process_cache(refs[bpmn_process_identifier])
                    return FileSystemService.full_path_to_process_model_file(process_model)
            except Exception:
                current_app.logger.warning("Failed to parse process ", process_model.id)
        return None

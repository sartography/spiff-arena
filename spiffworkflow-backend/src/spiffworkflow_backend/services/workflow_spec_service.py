from typing import NewType

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.file import FileType
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.spec_file_service import SpecFileService

from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore

IdToBpmnProcessSpecMapping = NewType("IdToBpmnProcessSpecMapping", dict[str, BpmnProcessSpec])

class WorkflowSpecService:
    
    @staticmethod
    def get_spec(
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
        ProcessInstanceProcessor.update_spiff_parser_with_all_process_dependency_files(parser)

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


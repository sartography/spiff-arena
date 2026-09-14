from pathlib import Path

from flask import current_app

from spiffworkflow_backend.models.bpmn_process_definition import BpmnProcessDefinitionModel
from spiffworkflow_backend.models.bpmn_process_definition_relationship import BpmnProcessDefinitionRelationshipModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.git_service import GitCommandError
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.model_source_service import ModelSourceService
from spiffworkflow_backend.services.model_source_service import ModelSourceUnavailableError


class ProcessInstanceDiagramUnavailableError(Exception):
    pass


class ProcessInstanceDiagramService:
    @classmethod
    def get_xml(cls, process_instance: ProcessInstanceModel, process_identifier: str | None = None) -> str:
        """Return only an instance's saved diagram or its recorded git revision.

        This read-only lookup deliberately avoids current model metadata and the
        reference cache: both can refer to a different version of the process.
        """
        if process_instance.source_manifest_id:
            try:
                path = ModelSourceService.process_path(process_instance, process_identifier)
                return ModelSourceService.read(process_instance.source_manifest_id, path).decode("utf-8")
            except ModelSourceUnavailableError as exception:
                raise ProcessInstanceDiagramUnavailableError(exception.message) from exception

        definition = process_instance.bpmn_process_definition
        if definition is None:
            raise ProcessInstanceDiagramUnavailableError("The instance has no saved workflow definition for its diagram.")

        if process_identifier and process_identifier != definition.bpmn_identifier:
            definition = (
                BpmnProcessDefinitionModel.query.join(
                    BpmnProcessDefinitionRelationshipModel,
                    BpmnProcessDefinitionModel.id == BpmnProcessDefinitionRelationshipModel.bpmn_process_definition_child_id,
                )
                .filter(
                    BpmnProcessDefinitionRelationshipModel.bpmn_process_definition_parent_id == definition.id,
                    BpmnProcessDefinitionModel.bpmn_identifier == process_identifier,
                )
                .first()
            )
            if definition is None:
                raise ProcessInstanceDiagramUnavailableError(
                    "The requested process is not part of the instance's saved definition."
                )

        xml = definition.properties_json.get("bpmn_xml")
        if xml:
            return str(xml)

        return cls._get_legacy_xml(process_instance, definition)

    @staticmethod
    def _get_legacy_xml(process_instance: ProcessInstanceModel, definition: BpmnProcessDefinitionModel) -> str:
        revision = process_instance.bpmn_version_control_identifier
        if not revision:
            raise ProcessInstanceDiagramUnavailableError(
                "The historical diagram is unavailable: this instance has neither saved BPMN XML nor a recorded revision."
            )

        # Spiff stores model-local filenames for local processes and absolute
        # paths for dependencies. Use that historical filename, not today's
        # primary file or reference-cache entry.
        filename = definition.properties_json.get("file")
        if not filename:
            raise ProcessInstanceDiagramUnavailableError("The saved definition does not identify its historical BPMN file.")
        path = Path(filename)
        model_identifier = process_instance.process_model_identifier
        if path.is_absolute():
            try:
                path = path.relative_to(Path(FileSystemService.root_path()).resolve())
            except ValueError as exception:
                raise ProcessInstanceDiagramUnavailableError(
                    "The historical BPMN file was stored under a different model directory and cannot be located safely."
                ) from exception
            model_identifier = path.parent.as_posix()
        elif path.parent != Path("."):
            raise ProcessInstanceDiagramUnavailableError("The saved definition has an unsupported historical BPMN file path.")

        model = ProcessModelInfo(id=model_identifier, display_name="", description="")
        try:
            # Always git show, even at HEAD or without a working git checkout.
            # The general GitService helper intentionally falls back to disk.
            return GitService.get_instance_file_contents_for_revision(model, revision, path.name)
        except (GitCommandError, OSError) as exception:
            current_app.logger.warning(
                "Failed to retrieve historical BPMN XML for instance %s: %s", process_instance.id, exception
            )
            raise ProcessInstanceDiagramUnavailableError(
                "Failed to retrieve historical BPMN XML from version control."
            ) from exception

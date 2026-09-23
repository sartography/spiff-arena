"""Instance-aware model inputs, independent of their storage provider."""

# Some service imports stay local while consumers are moved to lower-level APIs.
# ruff: noqa: PLC0415

import json
import os
from collections.abc import Iterable
from pathlib import PurePosixPath
from typing import TYPE_CHECKING
from typing import Protocol
from typing import cast

from flask import current_app
from flask import has_app_context
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore
from sqlalchemy.orm import Session

from spiffworkflow_backend.exceptions import process_entity_not_found_error
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.models.reference_cache import ReferenceCacheModel
from spiffworkflow_backend.models.reference_cache import ReferenceNotFoundError
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.services.task_service import TaskService

if TYPE_CHECKING:
    from spiffworkflow_backend.services.workflow_spec_service import IdToBpmnProcessSpecMapping


class SourceFiles(Protocol):
    """A complete source set. Missing files must not fall back to another source."""

    def paths(self) -> Iterable[str]: ...

    def read(self, path: str) -> bytes: ...


class ModelSourceProvider(Protocol):
    def open(self, session: Session, instance: ProcessInstanceModel) -> SourceFiles | None: ...

    def prepare(self, session: Session, instance: ProcessInstanceModel) -> SourceFiles | None:
        """Prepare new-instance inputs in the caller's transaction, without committing."""
        ...

    def assert_can_migrate(self, session: Session, instance: ProcessInstanceModel) -> None: ...


class ModelSource:
    """Interpret provider files, or use Arena's repository/Git loading behavior."""

    def __init__(self, instance: ProcessInstanceModel | None = None, files: SourceFiles | None = None):
        self.instance = instance
        self.files = files

    def model(self, identifier: str) -> ProcessModelInfo:
        from spiffworkflow_backend.services.process_model_service import ProcessModelService

        if self.files is None:
            return ProcessModelService.get_process_model(identifier)
        config = json.loads(self.files.read(f"{identifier}/process_model.json"))
        return ProcessModelInfo.from_dict({**config, "id": identifier})

    def specs(
        self, identifier: str, process_identifier: str | None = None
    ) -> tuple[BpmnProcessSpec, "IdToBpmnProcessSpecMapping"]:
        if self.files is None:
            from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService

            try:
                return BpmnProcessService.get_process_model_and_subprocesses(identifier, process_id_to_run=process_identifier)
            except ProcessEntityNotFoundError as exception:
                raise process_entity_not_found_error.ProcessEntityNotFoundError(str(exception)) from exception
        config = json.loads(self.files.read(f"{identifier}/process_model.json"))
        from spiffworkflow_backend.services.custom_parser import MyCustomParser

        paths = set(self.files.paths())
        parser = MyCustomParser()
        from spiffworkflow_backend.services.process_model_service import ProcessModelService

        for path in sorted(paths):
            if f"{PurePosixPath(path).parent}/process_model.json" not in paths:
                continue
            if path.endswith((".bpmn", ".dmn")):
                document = ProcessModelService.get_etree_from_xml_bytes(self.files.read(path))
                if path.endswith(".bpmn"):
                    parser.add_bpmn_xml(document, filename=path)
                else:
                    parser.add_dmn_xml(document, filename=path)
        process_identifier = process_identifier or config.get("primary_process_id")
        if not process_identifier:
            raise ValueError("Model source has no primary process ID")
        from spiffworkflow_backend.services.workflow_spec_service import IdToBpmnProcessSpecMapping

        return parser.get_spec(process_identifier), IdToBpmnProcessSpecMapping(parser.get_subprocess_specs(process_identifier))

    def process_path(self, identifier: str, process_identifier: str | None) -> str:
        if self.files is None:
            raise ValueError("Process path resolution requires a supplied file set")
        if process_identifier is None:
            config = json.loads(self.files.read(f"{identifier}/process_model.json"))
            process_identifier = config.get("primary_process_id")
        if not process_identifier:
            raise FileNotFoundError("Model source has no primary process ID")
        matches = []
        namespace = "{http://www.omg.org/spec/BPMN/20100524/MODEL}"
        from spiffworkflow_backend.services.process_model_service import ProcessModelService

        for path in self.files.paths():
            if not path.endswith(".bpmn"):
                continue
            root = ProcessModelService.get_etree_from_xml_bytes(self.files.read(path))
            elements = root.iter(*(namespace + name for name in ("process", "subProcess", "transaction", "adHocSubProcess")))
            if any(element.get("id") == process_identifier for element in elements):
                matches.append(path)
        if len(matches) > 1:
            raise FileNotFoundError(f"Ambiguous BPMN for process {process_identifier}: {sorted(matches)}")
        if not matches:
            raise FileNotFoundError(f"No BPMN source for process {process_identifier}")
        return matches[0]

    def task_file(self, process_identifier: str, filename: str) -> bytes:
        if self.files is None:
            raise ValueError("Task file resolution requires a supplied file set")
        if not filename or filename in (".", "..") or "/" in filename or "\\" in filename:
            raise ValueError(f"Form filename must be unqualified: {filename!r}")
        owner = PurePosixPath(self.process_path("", process_identifier)).parent
        return self.files.read((owner / filename).as_posix())

    def form_contents(self, model: ProcessModelInfo, filename: str, task: TaskModel | None, revision: str | None) -> str:
        if self.files is not None and task is not None:
            return self.task_file(task.bpmn_process.bpmn_process_definition.bpmn_identifier, filename).decode("utf-8")
        from spiffworkflow_backend.services.git_service import GitService

        return GitService.get_file_contents_for_revision_if_git_revision(
            process_model=model, revision=revision, file_name=filename
        )

    def model_for_task(self, model: ProcessModelInfo, task: TaskModel) -> ProcessModelInfo:
        # Supplied files resolve form ownership directly from the task's BPMN process.
        if self.files is not None:
            return model
        from spiffworkflow_backend.services.spec_file_service import SpecFileService

        process_identifier = task.bpmn_process.bpmn_process_definition.bpmn_identifier
        if process_identifier in [ref.identifier for ref in SpecFileService.get_references_for_process(model)]:
            return model
        top_process = TaskService.bpmn_process_for_called_activity_or_top_level_process(task)
        from spiffworkflow_backend.services.file_system_service import FileSystemService
        from spiffworkflow_backend.services.workflow_spec_service import WorkflowSpecService

        path = WorkflowSpecService.bpmn_file_full_path_from_bpmn_process_identifier(
            top_process.bpmn_process_definition.bpmn_identifier
        )
        relative_path = os.path.relpath(path, start=FileSystemService.root_path())
        from spiffworkflow_backend.services.process_model_service import ProcessModelService

        return ProcessModelService.get_process_model_from_relative_path(os.path.dirname(relative_path))

    def diagram(self, identifier: str, process_identifier: str | None) -> str:
        if self.files is None:
            raise ValueError("Diagram path resolution requires a supplied file set")
        return self.files.read(self.process_path(identifier, process_identifier)).decode("utf-8")

    def diagram_payload(self, instance: ProcessInstanceModel, process_identifier: str | None = None) -> dict:
        from spiffworkflow_backend.services.git_service import GitCommandError
        from spiffworkflow_backend.services.git_service import GitService
        from spiffworkflow_backend.services.process_model_service import ProcessModelService

        result: dict = {
            "bpmn_xml_file_contents": None,
            "bpmn_xml_file_contents_retrieval_error": None,
            "process_model_with_diagram_identifier": None,
        }
        if self.files is not None:
            try:
                result["bpmn_xml_file_contents"] = self.diagram(instance.process_model_identifier, process_identifier)
            except FileNotFoundError as error:
                result["bpmn_xml_file_contents_retrieval_error"] = str(error)
            return result

        model = None
        filename = None
        if process_identifier:
            reference = ReferenceCacheModel.basic_query().filter_by(identifier=process_identifier, type="process").first()
            if reference is None:
                raise ReferenceNotFoundError(f"Could not find given process identifier in the cache: {process_identifier}")
            model = ProcessModelService.get_process_model(reference.relative_location)
            filename = reference.file_name
            result["process_model_with_diagram_identifier"] = model.id
        else:
            try:
                model = ProcessModelService.get_process_model_or_raise_api_error(instance.process_model_identifier)
                filename = model.primary_file_name
            except Exception as error:
                current_app.logger.warning(f"Failed to retrieve process model for diagram: {error}")
                result["bpmn_xml_file_contents_retrieval_error"] = "Failed to retrieve process model for diagram."
        if model and filename:
            try:
                result["bpmn_xml_file_contents"] = GitService.get_file_contents_for_revision_if_git_revision(
                    process_model=model, revision=instance.bpmn_version_control_identifier, file_name=filename
                )
            except GitCommandError as error:
                current_app.logger.warning(f"Failed to retrieve BPMN XML from git: {error}")
                result["bpmn_xml_file_contents_retrieval_error"] = "Failed to retrieve BPMN XML from version control."
        return result


class ModelSources:
    @staticmethod
    def provider() -> ModelSourceProvider | None:
        if not has_app_context():  # type: ignore[no-untyped-call]
            return None
        return cast(ModelSourceProvider | None, current_app.extensions.get("model_sources"))

    @classmethod
    def for_instance(cls, instance: ProcessInstanceModel) -> ModelSource:
        provider = cls.provider()
        files = provider.open(db.session, instance) if provider is not None and instance.id is not None else None
        return ModelSource(instance, files)

    @classmethod
    def for_task(cls, task: TaskModel | None) -> ModelSource:
        if task is None or cls.provider() is None:
            return ModelSource()
        instance = ProcessInstanceModel.query.filter_by(id=task.process_instance_id).first()
        if instance is None:
            raise LookupError(f"Process instance {task.process_instance_id} does not exist")
        return cls.for_instance(instance)

    @classmethod
    def prepare_instance(cls, instance: ProcessInstanceModel, load_definition: bool = True) -> None:
        provider = cls.provider()
        files = None
        if provider is not None:
            db.session.flush()
            files = provider.prepare(db.session, instance)
        if load_definition or files is not None:
            source = ModelSource(instance, files)
            from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService

            BpmnProcessService.persist_bpmn_process_definition(
                instance.process_model_identifier, specs=source.specs(instance.process_model_identifier), commit=False
            )

    @classmethod
    def assert_can_migrate(cls, instance: ProcessInstanceModel) -> None:
        provider = cls.provider()
        if provider is not None:
            provider.assert_can_migrate(db.session, instance)

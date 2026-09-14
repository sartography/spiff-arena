import json
import mimetypes
import posixpath
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import TYPE_CHECKING

from flask import current_app
from lxml.etree import XMLSyntaxError  # type: ignore
from SpiffWorkflow.bpmn.parser.ValidationException import ValidationException  # type: ignore
from SpiffWorkflow.bpmn.specs.bpmn_process_spec import BpmnProcessSpec  # type: ignore

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.model_source import ModelSourceBlobModel
from spiffworkflow_backend.models.model_source import ModelSourceManifestModel
from spiffworkflow_backend.models.model_source import ModelSourceVersionModel
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.custom_parser import MyCustomParser
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.workflow_spec_service import IdToBpmnProcessSpecMapping
from spiffworkflow_backend.services.workflow_spec_service import WorkflowSpecService
from spiffworkflow_backend.utils.db_utils import insert_or_ignore_duplicate

if TYPE_CHECKING:
    from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
    from spiffworkflow_backend.models.task import TaskModel

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"


class ModelSourceUnavailableError(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__("model_source_unavailable", message, status_code=404)


class _SourceChangedDuringCaptureError(Exception):
    pass


@dataclass
class CapturedModelSources:
    manifest: dict
    files: dict[str, bytes]

    @property
    def digest(self) -> str:
        return sha256(json.dumps(self.manifest, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


class ModelSourceService:
    """Capture, resolve and read immutable model sources without involving engine serialization.

    A manifest is paired with a compiled definition on the instance. Neither
    definition hashes nor the current reference cache identify a source version.
    Mutations/commits belong to the caller; all instance reads are read-only.
    """

    @staticmethod
    def canonical_path(path: str) -> str:
        normalized = posixpath.normpath(path)
        if "\\" in path or normalized.startswith(("/", "../")) or normalized in (".", ".."):
            raise ModelSourceUnavailableError("Model source paths must stay within the model repository.")
        return normalized

    @classmethod
    def capture(cls, model_identifier: str) -> CapturedModelSources:
        ProcessModelService.get_process_model(model_identifier)
        for _attempt in range(3):
            try:
                return cls._capture_once(model_identifier)
            except _SourceChangedDuringCaptureError:
                continue
        raise ApiError(
            "model_sources_changed", "Model files changed during capture. Retry after saving the model.", status_code=409
        )

    @classmethod
    def _capture_once(cls, model_identifier: str) -> CapturedModelSources:
        root = Path(FileSystemService.root_path()).resolve()
        files: dict[str, bytes] = {}
        observations: dict[Path, tuple[int, int, int, int]] = {}
        parsed_files: list[str] = []
        models: dict[str, dict] = {}
        excluded: set[str] = set()
        parser = MyCustomParser()

        def fingerprint(path: Path) -> tuple[int, int, int, int]:
            try:
                stat = path.stat()
            except FileNotFoundError as exception:
                raise _SourceChangedDuringCaptureError() from exception
            return stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns

        def read(path: str) -> bytes:
            path = cls.canonical_path(path)
            absolute = root / path
            if not absolute.resolve().is_relative_to(root) or absolute.is_symlink():
                raise ModelSourceUnavailableError(f"Model source cannot be a link outside its repository: {path}")
            if path not in files:
                before = fingerprint(absolute)
                try:
                    files[path] = absolute.read_bytes()
                except FileNotFoundError as exception:
                    raise _SourceChangedDuringCaptureError() from exception
                if before != fingerprint(absolute):
                    raise _SourceChangedDuringCaptureError()
                observations[absolute] = before
            return files[path]

        def collect(directory: str) -> None:
            absolute = root / cls.canonical_path(directory)
            observations[absolute] = fingerprint(absolute)
            for child in sorted(absolute.iterdir()):
                if child.name.startswith(".") or child.name == "__pycache__" or child.is_symlink():
                    continue
                relative = child.relative_to(root).as_posix()
                if child.is_dir():
                    # Nested models are collected only when they participate.
                    if not (child / "process_model.json").exists():
                        collect(relative)
                elif relative not in excluded:
                    read(relative)

        def add_model(identifier: str) -> None:
            identifier = cls.canonical_path(identifier)
            if identifier in models:
                return
            config = json.loads(read(f"{identifier}/process_model.json"))
            config["id"] = identifier
            models[identifier] = config
            excluded.update(cls.canonical_path(f"{identifier}/{name}") for name in config.get("live_data_files", []))
            # Inspect the BPMN before collecting JSON so mutable file stores
            # never participate in a source version, even after their values change.
            directory = root / identifier
            observations[directory] = fingerprint(directory)
            bpmn_paths = sorted(directory.glob("*.bpmn"))
            for absolute in bpmn_paths:
                path = absolute.relative_to(root).as_posix()
                document = ProcessModelService.get_etree_from_xml_bytes(read(path))
                for store in document.findall(f"{{{BPMN_NS}}}dataStore"):
                    if store.get("name") == "JSONFileDataStore":
                        for parent in [Path(identifier), *Path(identifier).parents]:
                            excluded.add(cls.canonical_path((parent / f"{store.get('id')}.json").as_posix()))
                parser.add_bpmn_xml(document, filename=path)
                parsed_files.append(path)
            for absolute in sorted(directory.glob("*.dmn")):
                path = absolute.relative_to(root).as_posix()
                parser.add_dmn_xml(ProcessModelService.get_etree_from_xml_bytes(read(path)), filename=path)
                parsed_files.append(path)
            collect(identifier)
            for asset in config.get("source_assets", []):
                read(asset)
            for parent in Path(identifier).parents:
                group_path = (parent / "process_group.json").as_posix()
                if (root / group_path).is_file():
                    read(group_path)

        try:
            add_model(model_identifier)
            while True:
                dependencies = parser.get_process_dependencies() - {None} - set(parser.get_process_ids())
                if not dependencies:
                    break
                for identifier in sorted(dependencies):
                    path = Path(WorkflowSpecService.bpmn_file_full_path_from_bpmn_process_identifier(identifier)).resolve()
                    if not path.is_relative_to(root):
                        raise ModelSourceUnavailableError("A called process is outside the model repository.")
                    owner = path.parent.relative_to(root).as_posix()
                    if owner in models:
                        raise ModelSourceUnavailableError(f"The model files do not contain called process {identifier}.")
                    add_model(owner)
            scripts_dir = current_app.config.get("SPIFFWORKFLOW_BACKEND_GLOBAL_SCRIPTS_DIR")
            if scripts_dir and (root / cls.canonical_path(scripts_dir)).is_dir():
                collect(scripts_dir)
        except XMLSyntaxError as exception:
            raise ApiError.from_invalid_xml(model_identifier, exception) from exception

        for path, observed in observations.items():
            if fingerprint(path) != observed:
                raise _SourceChangedDuringCaptureError()
        for excluded_path in excluded:
            files.pop(excluded_path, None)

        processes = {identifier: process.filename for identifier, process in parser.process_parsers.items()}
        manifest = {
            "version": 1,
            "root_model": model_identifier,
            "models": models,
            "processes": processes,
            "decisions": {identifier: decision.filename for identifier, decision in parser.dmn_parsers.items()},
            "parsed_files": parsed_files,
            "files": {
                path: {
                    "digest": sha256(data).hexdigest(),
                    "content_type": cls.content_type(path),
                    "size": len(data),
                }
                for path, data in sorted(files.items())
            },
        }
        return CapturedModelSources(manifest, files)

    @staticmethod
    def content_type(path: str) -> str:
        suffix = Path(path).suffix
        if suffix in (".bpmn", ".dmn", ".xml"):
            return "application/xml"
        if suffix in (".md", ".py", ".sql", ".txt"):
            return "text/plain"
        return mimetypes.guess_type(path)[0] or "application/octet-stream"

    @classmethod
    def parse(
        cls, sources: CapturedModelSources, process_id: str | None = None
    ) -> tuple[BpmnProcessSpec, IdToBpmnProcessSpecMapping]:
        parser = MyCustomParser()
        for path in sources.manifest["parsed_files"]:
            document = ProcessModelService.get_etree_from_xml_bytes(sources.files[path])
            if path.endswith(".bpmn"):
                parser.add_bpmn_xml(document, filename=path)
            else:
                parser.add_dmn_xml(document, filename=path)
        process_id = process_id or sources.manifest["models"][sources.manifest["root_model"]].get("primary_process_id")
        if not process_id:
            raise ApiError("no_primary_bpmn_error", "There is no primary BPMN process id defined for the model.")
        try:
            spec = parser.get_spec(process_id)
            subprocesses = parser.get_subprocess_specs(process_id)
        except ValidationException as exception:
            raise ApiError(
                "process_instance_validation_error",
                f"Failed to parse the Workflow Specification: {exception}",
                file_name=exception.file_name,
                task_name=exception.name,
                task_id=exception.id,
                tag=exception.tag,
            ) from exception
        return spec, IdToBpmnProcessSpecMapping(subprocesses)

    @classmethod
    def store(cls, sources: CapturedModelSources, definition_id: int | None = None) -> str:
        digest = sources.digest
        if ModelSourceManifestModel.query.filter_by(digest=digest).first() is None:
            for path, data in sources.files.items():
                insert_or_ignore_duplicate(
                    ModelSourceBlobModel, {"digest": sources.manifest["files"][path]["digest"], "contents": data}
                )
            insert_or_ignore_duplicate(ModelSourceManifestModel, {"digest": digest, "manifest": sources.manifest})
        if definition_id is not None:
            cls.associate(digest, definition_id)
        return digest

    @staticmethod
    def associate(digest: str, definition_id: int) -> None:
        insert_or_ignore_duplicate(ModelSourceVersionModel, {"definition_id": definition_id, "manifest_digest": digest})

    @classmethod
    def sources_for_definition(
        cls, definition_id: int, model_identifier: str, digest: str | None = None
    ) -> CapturedModelSources | None:
        versions = ModelSourceVersionModel.query.filter_by(definition_id=definition_id).all()
        candidates = [
            version.manifest_digest
            for version in versions
            if cls.manifest(version.manifest_digest)["root_model"] == model_identifier
        ]
        if digest is not None:
            if digest not in candidates:
                raise ModelSourceUnavailableError("The selected source version does not belong to the target definition.")
            return cls.load(digest)
        if len(candidates) > 1:
            raise ApiError(
                "ambiguous_model_source_version", "This definition has several source versions. Select target_source_manifest_id."
            )
        return cls.load(candidates[0]) if candidates else None

    @staticmethod
    def manifest(digest: str | None) -> dict:
        # Reads during engine execution must not flush pending task/instance
        # changes and hold a write lock across an external service call.
        with db.session.no_autoflush:
            record = ModelSourceManifestModel.query.filter_by(digest=digest).first() if digest else None
        if record is None:
            raise ModelSourceUnavailableError("This instance has no saved model source files.")
        return dict(record.manifest)

    @classmethod
    def read(cls, digest: str | None, path: str) -> bytes:
        manifest = cls.manifest(digest)
        path = cls.canonical_path(path)
        entry = manifest["files"].get(path)
        if entry is None:
            raise ModelSourceUnavailableError(f"The historical model does not contain file {path}.")
        with db.session.no_autoflush:
            blob = ModelSourceBlobModel.query.filter_by(digest=entry["digest"]).first()
        if blob is None:
            raise ModelSourceUnavailableError(f"The saved contents of {path} are unavailable.")
        return bytes(blob.contents)

    @classmethod
    def load(cls, digest: str) -> CapturedModelSources:
        manifest = cls.manifest(digest)
        # Parsing needs only BPMN/DMN. Large documents/images stay out of runtime memory.
        return CapturedModelSources(manifest, {path: cls.read(digest, path) for path in manifest["parsed_files"]})

    @classmethod
    def process_path(cls, instance: "ProcessInstanceModel", process_identifier: str | None = None) -> str:
        manifest = cls.manifest(instance.source_manifest_id)
        process_identifier = process_identifier or (
            instance.bpmn_process_definition.bpmn_identifier
            if instance.bpmn_process_definition
            else manifest["models"][manifest["root_model"]]["primary_process_id"]
        )
        path = manifest["processes"].get(process_identifier)
        if path is None:
            raise ModelSourceUnavailableError("The requested process is not in this instance's source manifest.")
        return str(path)

    @classmethod
    def model_for_instance(cls, instance: "ProcessInstanceModel", process_identifier: str | None = None) -> ProcessModelInfo:
        if not instance.source_manifest_id:
            return ProcessModelService.get_process_model(instance.process_model_identifier)
        manifest = cls.manifest(instance.source_manifest_id)
        owner = str(Path(cls.process_path(instance, process_identifier)).parent) if process_identifier else manifest["root_model"]
        return ProcessModelInfo.from_dict(manifest["models"][owner])

    @classmethod
    def task_file_path(cls, task: "TaskModel", filename: str) -> str:
        process_id = task.bpmn_process.bpmn_process_definition.bpmn_identifier
        path = cls.process_path(task.process_instance, process_id)
        return cls.canonical_path(posixpath.join(posixpath.dirname(path), filename))

    @classmethod
    def files_for_instance(cls, instance: "ProcessInstanceModel") -> list[dict]:
        if not instance.source_manifest_id:
            return []
        return [{"path": path, **metadata} for path, metadata in cls.manifest(instance.source_manifest_id)["files"].items()]

import json
import re
import time
from dataclasses import dataclass
from typing import Any
from typing import cast

import requests
from flask import current_app
from lxml import etree  # type: ignore

from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


@dataclass
class ImportError(Exception):
    """Base class for import-related exceptions."""

    message: str
    error_code: str


class InvalidGitHubUrlError(ImportError):
    """Exception raised when a GitHub URL is invalid."""


class GitHubRepositoryNotFoundError(ImportError):
    """Exception raised when a GitHub repository is not found."""


class InvalidProcessModelError(ImportError):
    """Exception raised when a repository does not contain a valid process model."""


class InvalidModelAliasError(ImportError):
    """Exception raised when a model alias is invalid."""


class ModelAliasNotFoundError(ImportError):
    """Exception raised when a model with the specified alias is not found."""


class ModelMarketplaceError(ImportError):
    """Exception raised when there are issues communicating with the model marketplace."""


class InvalidFilestorePackageError(ImportError):
    """Exception raised when a Files package cannot be imported."""


class ProcessModelImportService:
    @classmethod
    def import_filestore_file_update(cls, payload: dict[str, Any], process_group_id: str) -> list[ProcessModelInfo]:
        raw_file = payload.get("file")
        file = raw_file if isinstance(raw_file, dict) else {}
        path = file.get("path")
        content = file.get("content")
        if not isinstance(path, str) or content is None:
            raise InvalidFilestorePackageError(
                message="Files update payload must include file.path and file.content",
                error_code="invalid_filestore_package",
            )

        return cls.import_from_filestore_package(
            {
                "project_id": payload.get("project_id"),
                "project_name": payload.get("project_name"),
                "files": [{"path": path, "content": str(content)}],
            },
            process_group_id,
        )

    @classmethod
    def import_from_filestore_package(cls, package: dict[str, Any], process_group_id: str) -> list[ProcessModelInfo]:
        process_group = cls._ensure_process_group(process_group_id)
        files = cls._filestore_files(package)
        model_dirs = cls._filestore_model_dirs(files)
        process_models = []

        for model_dir in model_dirs:
            model_files = cls._filestore_files_for_model_dir(files, model_dir, model_dirs)
            if not model_files:
                continue

            model_id = cls._filestore_model_id(package, model_dir)
            full_process_model_id = f"{process_group.id}/{model_id}"
            parent_group_id = "/".join(full_process_model_id.split("/")[:-1])
            cls._ensure_process_group(parent_group_id)

            existing_model = ProcessModelService.is_process_model_identifier(full_process_model_id)
            has_model_json = "process_model.json" in model_files
            model_info = cls._extract_process_model_info(model_files) if has_model_json or not existing_model else {}

            if existing_model:
                process_model = ProcessModelService.get_process_model(full_process_model_id)
                if has_model_json:
                    cls._update_process_model_from_filestore_info(process_model, model_info)
            else:
                display_name = model_info.get("display_name", cls._filestore_display_name(package, model_id, model_dir))
                description = model_info.get(
                    "description",
                    f"Imported from Files project {package.get('project_id')} snapshot {package.get('snapshot_id')}",
                )
                process_model = ProcessModelInfo(
                    id=full_process_model_id,
                    display_name=display_name,
                    description=description,
                )
                ProcessModelService.add_process_model(process_model)

            for file_name, file_content in model_files.items():
                if file_name == "process_model.json":
                    continue
                SpecFileService.update_file(process_model, file_name, file_content)

            if not existing_model and model_info.get("primary_file_name"):
                process_model.primary_file_name = model_info.get("primary_file_name")

            if not existing_model and model_info.get("primary_process_id"):
                process_model.primary_process_id = model_info.get("primary_process_id")

            if not existing_model and model_info:
                ProcessModelService.update_process_model(process_model, {})
            process_models.append(process_model)

        if not process_models:
            raise InvalidFilestorePackageError(
                message="Files package did not contain an importable process model",
                error_code="invalid_filestore_package",
            )

        return process_models

    @classmethod
    def _update_process_model_from_filestore_info(
        cls,
        process_model: ProcessModelInfo,
        model_info: dict[str, Any],
    ) -> None:
        updates = {}
        for key in ("display_name", "description", "primary_file_name", "primary_process_id"):
            if key in model_info and getattr(process_model, key) != model_info[key]:
                updates[key] = model_info[key]

        if updates:
            ProcessModelService.update_process_model(process_model, updates)

    @classmethod
    def _ensure_process_group(cls, process_group_id: str) -> ProcessGroup:
        if ProcessModelService.is_process_group_identifier(process_group_id):
            return ProcessModelService.get_process_group(process_group_id)

        parent_group_id = "/".join(process_group_id.split("/")[:-1])
        if parent_group_id:
            cls._ensure_process_group(parent_group_id)

        return ProcessModelService.add_process_group(
            ProcessGroup(
                id=process_group_id,
                display_name=process_group_id.rsplit("/", maxsplit=1)[-1].replace("-", " ").title(),
            )
        )

    @classmethod
    def _filestore_files(cls, package: dict[str, Any]) -> dict[str, bytes]:
        raw_files = package.get("files")
        if not isinstance(raw_files, list):
            raise InvalidFilestorePackageError(
                message="Files package must include a files array",
                error_code="invalid_filestore_package",
            )

        files = {}
        for raw_file in raw_files:
            path = raw_file.get("path") if isinstance(raw_file, dict) else None
            content = raw_file.get("content") if isinstance(raw_file, dict) else None
            if not isinstance(path, str) or content is None:
                continue
            cls._validate_filestore_path(path)
            files[path] = str(content).encode("utf-8")

        if not files:
            raise InvalidFilestorePackageError(
                message="Files package did not include any files",
                error_code="invalid_filestore_package",
            )

        return files

    @staticmethod
    def _validate_filestore_path(path: str) -> None:
        parts = path.split("/")
        if path.startswith("/") or "" in parts or ".." in parts:
            raise InvalidFilestorePackageError(
                message=f"Invalid Files package path: {path}",
                error_code="invalid_filestore_package",
            )

    @classmethod
    def _filestore_model_dirs(cls, files: dict[str, bytes]) -> list[str]:
        explicit_dirs = {
            cls._dirname(path) for path in files if path.endswith("/process_model.json") or path == "process_model.json"
        }
        if explicit_dirs:
            return sorted(explicit_dirs)

        bpmn_dirs = {cls._dirname(path) for path in files if path.endswith(".bpmn")}
        if not bpmn_dirs:
            raise InvalidFilestorePackageError(
                message="Files package must contain at least one BPMN file",
                error_code="invalid_filestore_package",
            )

        if bpmn_dirs == {""}:
            return [""]

        return sorted(bpmn_dirs)

    @staticmethod
    def _dirname(path: str) -> str:
        return path.rsplit("/", 1)[0] if "/" in path else ""

    @classmethod
    def _filestore_files_for_model_dir(
        cls,
        files: dict[str, bytes],
        model_dir: str,
        model_dirs: list[str],
    ) -> dict[str, bytes]:
        model_files = {}
        for path, content in files.items():
            owner = cls._filestore_owner_model_dir(path, model_dirs)
            if owner != model_dir:
                continue

            file_name = path.removeprefix(f"{model_dir}/") if model_dir else path
            if file_name == "process_group.json":
                continue
            model_files[file_name] = content

        return model_files

    @classmethod
    def _filestore_owner_model_dir(cls, path: str, model_dirs: list[str]) -> str:
        owners = [model_dir for model_dir in model_dirs if path == model_dir or path.startswith(f"{model_dir}/")]
        if "" in model_dirs and "/" not in path:
            owners.append("")
        return max(owners, key=len) if owners else ""

    @classmethod
    def _filestore_model_id(cls, package: dict[str, Any], model_dir: str) -> str:
        if model_dir:
            return "/".join(cls._slug(segment) for segment in model_dir.split("/"))
        return cls._filestore_root_model_id(package)

    @classmethod
    def _filestore_root_model_id(cls, package: dict[str, Any]) -> str:
        project_id = cls._slug(str(package.get("project_id") or package.get("label") or "filestore-project"))
        project_name = package.get("project_name")
        if not isinstance(project_name, str) or not project_name.strip():
            return project_id

        project_name = cls._slug(project_name)
        return project_id if project_id.startswith(f"{project_name}-") else f"{project_name}-{project_id}"

    @classmethod
    def _filestore_display_name(cls, package: dict[str, Any], model_id: str, model_dir: str) -> str:
        project_name = package.get("project_name")
        project_id = package.get("project_id")
        if not model_dir and isinstance(project_name, str) and project_name.strip():
            display_name = project_name.strip()
            if isinstance(project_id, str) and project_id.strip() and project_id.strip() not in display_name:
                display_name = f"{display_name} {project_id.strip()}"
            return display_name

        return model_id.rsplit("/", maxsplit=1)[-1].replace("-", " ").title()

    @staticmethod
    def _slug(text: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", text).strip("-").lower()
        return slug or "filestore-project"

    @classmethod
    def import_from_github_url(cls, url: str, process_group_id: str) -> ProcessModelInfo:
        process_group = ProcessModelService.get_process_group(process_group_id)

        repo_info = cls._parse_github_url(url)
        files = cls._fetch_files_from_github(repo_info)
        model_info = cls._extract_process_model_info(files)
        model_id = model_info.get("id") or cls._generate_id_from_url(url)
        full_process_model_id = f"{process_group.id}/{model_id}"

        if ProcessModelService.is_process_model_identifier(full_process_model_id):
            model_id = f"{model_id}-{int(time.time())}"
            full_process_model_id = f"{process_group.id}/{model_id}"

        display_name = model_info.get("display_name", model_id.replace("-", " ").title())
        description = model_info.get("description", f"Imported from {url}")
        process_model = ProcessModelInfo(id=full_process_model_id, display_name=display_name, description=description)
        ProcessModelService.add_process_model(process_model)

        timestamp = int(time.time())
        for file_name, file_content in files.items():
            # Make BPMN process IDs unique to avoid conflicts
            file_content_to_save = file_content
            if file_name.endswith(".bpmn"):
                file_content_to_save = cls._make_bpmn_process_ids_unique(file_content, timestamp)
            SpecFileService.update_file(process_model, file_name, file_content_to_save)

        if model_info.get("primary_file_name"):
            process_model.primary_file_name = model_info.get("primary_file_name")

        if model_info.get("primary_process_id"):
            original_primary_process_id = model_info.get("primary_process_id")
            updated_primary_process_id = f"{original_primary_process_id}_{timestamp}" if original_primary_process_id else None
            process_model.primary_process_id = updated_primary_process_id

        ProcessModelService.update_process_model(process_model, {})

        return process_model

    @classmethod
    def _parse_github_url(cls, url: str) -> dict[str, str]:
        """Parse a GitHub URL to extract repository information."""
        # Example URL: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example

        github_regex = r"https://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/([^/]+)/(.+)"
        match = re.match(github_regex, url)
        if not match:
            raise InvalidGitHubUrlError(message=f"Invalid GitHub URL format: {url}", error_code="invalid_github_url_error")

        owner, repo, branch, path = match.groups()

        return {"owner": owner, "repo": repo, "branch": branch, "path": path, "type": "tree" if "/tree/" in url else "blob"}

    @classmethod
    def _fetch_files_from_github(cls, repo_info: dict[str, str]) -> dict[str, bytes]:
        api_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/contents/{repo_info['path']}?ref={repo_info['branch']}"
        response = requests.get(api_url, timeout=30)
        if response.status_code != 200:
            raise GitHubRepositoryNotFoundError(
                message=f"GitHub API error: {response.status_code}", error_code="git_hub_repository_not_found_error"
            )

        contents = response.json()

        if not isinstance(contents, list):
            if repo_info["type"] == "blob":
                file_content = cls._download_file(contents["download_url"])
                return {contents["name"]: file_content}
            else:
                raise InvalidProcessModelError(
                    message="URL points to a file, not a directory", error_code="invalid_process_model"
                )

        files = {}
        for item in contents:
            if item["type"] == "file":
                file_content = cls._download_file(item["download_url"])
                files[item["name"]] = file_content

        if not files:
            raise InvalidProcessModelError(message="No files found in the repository", error_code="invalid_process_model")

        return files

    @classmethod
    def _download_file(cls, url: str) -> bytes:
        response = requests.get(url, timeout=30)
        if response.status_code != 200:
            raise GitHubRepositoryNotFoundError(
                message=f"Failed to download file: {response.status_code}", error_code="github_repository_not_found_error"
            )

        return response.content

    @classmethod
    def _extract_process_model_info(cls, files: dict[str, bytes]) -> dict[str, Any]:
        model_info = {}

        if "process_model.json" in files:
            model_info = json.loads(files["process_model.json"].decode("utf-8"))

        if "primary_file_name" not in model_info:
            for file_name in files.keys():
                if file_name.endswith(".bpmn"):
                    model_info["primary_file_name"] = file_name
                    break

        if "primary_file_name" in model_info and "primary_process_id" not in model_info:
            primary_file_name = model_info["primary_file_name"]
            if primary_file_name in files:
                try:
                    process_id = cls._extract_process_id_from_bpmn(files[primary_file_name])
                    if process_id:
                        model_info["primary_process_id"] = process_id
                except Exception as ex:
                    current_app.logger.warning(f"Failed to extract process ID from BPMN: {str(ex)}")

        return model_info

    @classmethod
    def _extract_process_id_from_bpmn(cls, bpmn_content: bytes) -> str | None:
        try:
            # Use secure XML parser with entity resolution disabled
            etree_xml_parser = etree.XMLParser(resolve_entities=False, remove_comments=True, no_network=True)
            root = etree.fromstring(bpmn_content, parser=etree_xml_parser)  # noqa: S320
            ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
            process_elements = root.findall(".//bpmn:process", ns)
            if process_elements and "id" in process_elements[0].attrib:
                process_id = process_elements[0].get("id")
                return str(process_id) if process_id is not None else None
        except etree.ParseError:
            pass

        return None

    @classmethod
    def _make_bpmn_process_ids_unique(cls, bpmn_content: bytes, timestamp: int) -> bytes:
        """Make all process IDs in BPMN content unique by appending a timestamp."""
        try:
            etree_xml_parser = etree.XMLParser(resolve_entities=False, remove_comments=True, no_network=True)
            root = etree.fromstring(bpmn_content, parser=etree_xml_parser)  # noqa: S320
            ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
            process_elements = root.findall(".//bpmn:process", ns)

            for process_element in process_elements:
                if "id" in process_element.attrib:
                    old_id = process_element.get("id")
                    if old_id:
                        new_id = f"{old_id}_{timestamp}"
                        process_element.set("id", new_id)

            return cast(bytes, etree.tostring(root, encoding="utf-8"))

        except etree.ParseError:
            return bpmn_content

    @classmethod
    def _generate_id_from_url(cls, url: str) -> str:
        # Example URL: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example
        path_parts = url.strip("/").split("/")
        if path_parts:
            base_id = path_parts[-1]
            clean_id = re.sub(r"[^a-zA-Z0-9_-]", "-", base_id)
            return clean_id.lower()

        # Fallback to timestamp-based ID
        return f"imported-model-{int(time.time())}"

    @classmethod
    def is_valid_github_url(cls, url: str) -> bool:
        try:
            cls._parse_github_url(url)
            return True
        except InvalidGitHubUrlError:
            return False

    @classmethod
    def is_model_alias(cls, text: str) -> bool:
        """Check if the given text is a model alias (not a URL).

        A model alias is a simple string without URL-specific characters.
        """
        if text.startswith(("http://", "https://")):
            return False

        # If it contains slashes, colons, or other URL characters, it's probably not an alias
        if re.search(r"[/:?&=]", text):
            return False

        # Check for valid alias format (alphanumeric with hyphens, underscores)
        return bool(re.match(r"^[a-zA-Z0-9_-]+$", text))

    @classmethod
    def get_marketplace_url(cls) -> str:
        return str(current_app.config["SPIFFWORKFLOW_BACKEND_MODEL_MARKETPLACE_URL"])

    @classmethod
    def import_from_model_alias(cls, alias: str, process_group_id: str) -> ProcessModelInfo:
        process_group = ProcessModelService.get_process_group(process_group_id)

        files = cls._fetch_files_from_marketplace(alias)
        model_info = cls._extract_process_model_info(files)

        model_id = model_info.get("id") or alias
        full_process_model_id = f"{process_group.id}/{model_id}"

        if ProcessModelService.is_process_model_identifier(full_process_model_id):
            model_id = f"{model_id}-{int(time.time())}"
            full_process_model_id = f"{process_group.id}/{model_id}"

        display_name = model_info.get("display_name", model_id.replace("-", " ").title())
        description = model_info.get("description", f"Imported from marketplace: {alias}")
        process_model = ProcessModelInfo(id=full_process_model_id, display_name=display_name, description=description)
        ProcessModelService.add_process_model(process_model)

        timestamp = int(time.time())
        for file_name, file_content in files.items():
            # Make BPMN process IDs unique to avoid conflicts
            file_content_to_save = file_content
            if file_name.endswith(".bpmn"):
                file_content_to_save = cls._make_bpmn_process_ids_unique(file_content, timestamp)
            SpecFileService.update_file(process_model, file_name, file_content_to_save)

        if model_info.get("primary_file_name"):
            process_model.primary_file_name = model_info.get("primary_file_name")

        if model_info.get("primary_process_id"):
            original_primary_process_id = model_info.get("primary_process_id")
            updated_primary_process_id = f"{original_primary_process_id}_{timestamp}" if original_primary_process_id else None
            process_model.primary_process_id = updated_primary_process_id

        ProcessModelService.update_process_model(process_model, {})

        return process_model

    @classmethod
    def _fetch_files_from_marketplace(cls, alias: str) -> dict[str, bytes]:
        marketplace_url = cls.get_marketplace_url()
        api_url = f"{marketplace_url}/api/models/{alias}?include_files=true"

        try:
            response = requests.get(api_url, timeout=30)
            if response.status_code == 404:
                raise ModelAliasNotFoundError(
                    message=f"Model with alias '{alias}' not found in the marketplace", error_code="model_alias_not_found_error"
                )
            elif response.status_code != 200:
                raise ModelMarketplaceError(
                    message=f"Marketplace API error: {response.status_code}", error_code="model_marketplace_error"
                )

            data = response.json()
            if not data or "included" not in data:
                raise ModelMarketplaceError(
                    message="Invalid response format from marketplace API", error_code="invalid_marketplace_response"
                )

            files = {}
            # Extract files from the marketplace response
            for item in data.get("included", []):
                if item.get("type") == "process-model-files" and "attributes" in item:
                    attrs = item["attributes"]
                    if "file_name" in attrs and "content" in attrs:
                        file_name = attrs["file_name"]
                        file_content = attrs["content"].encode("utf-8")
                        files[file_name] = file_content

            if not files:
                raise InvalidProcessModelError(
                    message="No files found in the marketplace response", error_code="invalid_process_model"
                )

            return files

        except requests.RequestException as ex:
            raise ModelMarketplaceError(
                message=f"Error connecting to marketplace: {str(ex)}", error_code="marketplace_connection_error"
            ) from ex

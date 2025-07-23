import json
import re
import time
from dataclasses import dataclass
from typing import Any
from typing import cast

import requests
from flask import current_app
from lxml import etree  # type: ignore

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


class ProcessModelImportService:
    """Service for importing process models from external sources."""

    @classmethod
    def import_from_github_url(cls, url: str, process_group_id: str) -> ProcessModelInfo:
        """Import a process model from a GitHub URL.

        Args:
            url: The GitHub URL to import from
            process_group_id: The ID of the process group to import into

        Returns:
            ProcessModelInfo: The imported process model

        Raises:
            GitHubRepositoryNotFoundError: If the GitHub repository was not found
            InvalidProcessModelError: If the repository does not contain a valid process model
        """
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
        """Extract process model information from the files."""
        model_info = {}

        if "process_model.json" in files:
            model_info = json.loads(files["process_model.json"].decode("utf-8"))

        # Look for BPMN files to determine primary file if not in JSON
        if "primary_file_name" not in model_info:
            for file_name in files.keys():
                if file_name.endswith(".bpmn"):
                    model_info["primary_file_name"] = file_name
                    break

        # Extract process ID from BPMN if available
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
        """Make all process IDs in BPMN content unique by appending a timestamp.
        Args:
            bpmn_content: The original BPMN file content
            timestamp: A timestamp to append to process IDs
        Returns:
            bytes: The modified BPMN content with unique process IDs
        """
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

            # Return the modified XML
            return cast(bytes, etree.tostring(root, encoding="utf-8"))

        except etree.ParseError:
            return bpmn_content

    @classmethod
    def _generate_id_from_url(cls, url: str) -> str:
        """Generate a process model ID from the GitHub URL."""
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

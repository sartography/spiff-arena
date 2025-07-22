"""ProcessModelImportService."""
import re
import time
import json
import xml.etree.ElementTree as ET
import requests
from flask import current_app

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.file import File
from spiffworkflow_backend.models.process_model import ProcessModelInfo
from spiffworkflow_backend.services.git_service import GitService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.process_group_service import ProcessGroupService
from spiffworkflow_backend.services.spec_file_service import SpecFileService


class ImportError(Exception):
    """Base class for import-related exceptions."""


class InvalidGitHubUrlError(ImportError):
    """Exception raised when a GitHub URL is invalid."""


class GitHubRepositoryNotFoundError(ImportError):
    """Exception raised when a GitHub repository is not found."""


class InvalidProcessModelError(ImportError):
    """Exception raised when a repository does not contain a valid process model."""


class ProcessGroupNotFoundError(ImportError):
    """Exception raised when a process group is not found."""


class ProcessModelImportService:
    """Service for importing process models from external sources."""

    @classmethod
    def import_from_github_url(cls, url, process_group_id):
        """Import a process model from a GitHub URL.
        
        Args:
            url: The GitHub URL to import from
            process_group_id: The ID of the process group to import into
            
        Returns:
            ProcessModelInfo: The imported process model
            
        Raises:
            ProcessGroupNotFoundError: If the process group does not exist
            GitHubRepositoryNotFoundError: If the GitHub repository was not found
            InvalidProcessModelError: If the repository does not contain a valid process model
        """
        # Check if process group exists
        if not ProcessGroupService.process_group_exists(process_group_id):
            raise ProcessGroupNotFoundError(f"Process group not found: {process_group_id}")
        
        # Parse GitHub URL to get repository info
        repo_info = cls._parse_github_url(url)
        
        # Fetch the files from GitHub
        files = cls._fetch_files_from_github(repo_info)
        
        # Extract process model info from files
        model_info = cls._extract_process_model_info(files)
        
        # Determine process model ID
        model_id = model_info.get("id") or cls._generate_id_from_url(url)
        
        # Check for existing process model
        full_process_model_id = f"{process_group_id}/{model_id}"
        # If process model ID already exists, append timestamp to make it unique
        if ProcessModelService.process_model_exists(full_process_model_id):
            model_id = f"{model_id}-{int(time.time())}"
            full_process_model_id = f"{process_group_id}/{model_id}"
        
        # Create process model
        display_name = model_info.get("display_name", model_id.replace("-", " ").title())
        description = model_info.get("description", f"Imported from {url}")
        
        process_model = ProcessModelInfo(
            id=full_process_model_id,
            display_name=display_name,
            description=description
        )
        
        # Add the process model to the system
        process_model = ProcessModelService.add_process_model(process_model)
        
        # Add files to the process model
        for file_name, file_contents in files.items():
            file_data = File(
                name=file_name,
                content=file_contents,
                mimetype=cls._determine_mimetype(file_name)
            )
            SpecFileService.update_file(process_model.id, file_data)
        
        # Update primary file and process ID if found
        if model_info.get("primary_file_name"):
            process_model.primary_file_name = model_info.get("primary_file_name")
            
        if model_info.get("primary_process_id"):
            process_model.primary_process_id = model_info.get("primary_process_id")
            
        ProcessModelService.update_process_model(process_model)
        
        # Commit changes to Git
        cls._commit_to_git(process_model.id, f"Imported process model from {url}")
        
        return process_model
    
    @classmethod
    def _parse_github_url(cls, url):
        """Parse a GitHub URL to extract repository information."""
        # Example URL: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example
        
        # Validate URL format
        github_regex = r"https://github\.com/([^/]+)/([^/]+)/(?:tree|blob)/([^/]+)/(.+)"
        match = re.match(github_regex, url)
        if not match:
            raise InvalidGitHubUrlError(f"Invalid GitHub URL format: {url}")
        
        owner, repo, branch, path = match.groups()
        
        return {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "path": path,
            "type": "tree" if "/tree/" in url else "blob"
        }
    
    @classmethod
    def _fetch_files_from_github(cls, repo_info):
        """Fetch files from GitHub using the GitHub API."""
        # Construct GitHub API URL
        api_url = f"https://api.github.com/repos/{repo_info['owner']}/{repo_info['repo']}/contents/{repo_info['path']}?ref={repo_info['branch']}"
        
        # Make request to GitHub API
        response = requests.get(api_url)
        if response.status_code != 200:
            raise GitHubRepositoryNotFoundError(f"GitHub API error: {response.status_code}")
        
        # Parse response
        contents = response.json()
        
        # If response is a single file (not a directory)
        if not isinstance(contents, list):
            if repo_info["type"] == "blob":
                # Download the single file
                file_content = cls._download_file(contents["download_url"])
                return {contents["name"]: file_content}
            else:
                raise InvalidProcessModelError("URL points to a file, not a directory")
        
        # Download all files in the directory
        files = {}
        for item in contents:
            if item["type"] == "file":
                file_content = cls._download_file(item["download_url"])
                files[item["name"]] = file_content
        
        # Ensure we have at least one file
        if not files:
            raise InvalidProcessModelError("No files found in the repository")
        
        return files
    
    @classmethod
    def _download_file(cls, url):
        """Download a file from a URL."""
        response = requests.get(url)
        if response.status_code != 200:
            raise GitHubRepositoryNotFoundError(f"Failed to download file: {response.status_code}")
        
        return response.content
    
    @classmethod
    def _extract_process_model_info(cls, files):
        """Extract process model information from the files."""
        model_info = {}
        
        # Look for process_model.json
        if "process_model.json" in files:
            try:
                json_content = json.loads(files["process_model.json"].decode("utf-8"))
                if "id" in json_content:
                    model_info["id"] = json_content["id"]
                if "display_name" in json_content:
                    model_info["display_name"] = json_content["display_name"]
                if "description" in json_content:
                    model_info["description"] = json_content["description"]
                if "primary_file_name" in json_content:
                    model_info["primary_file_name"] = json_content["primary_file_name"]
                if "primary_process_id" in json_content:
                    model_info["primary_process_id"] = json_content["primary_process_id"]
            except json.JSONDecodeError:
                # If JSON parsing fails, just continue without the info
                pass
        
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
                except:
                    # If BPMN parsing fails, just continue without the process ID
                    pass
        
        return model_info
    
    @classmethod
    def _extract_process_id_from_bpmn(cls, bpmn_content):
        """Extract the process ID from BPMN content."""
        try:
            root = ET.fromstring(bpmn_content)
            ns = {"bpmn": "http://www.omg.org/spec/BPMN/20100524/MODEL"}
            process_elements = root.findall(".//bpmn:process", ns)
            if process_elements and "id" in process_elements[0].attrib:
                return process_elements[0].get("id")
        except ET.ParseError:
            pass
        
        return None
    
    @classmethod
    def _generate_id_from_url(cls, url):
        """Generate a process model ID from the GitHub URL."""
        # Extract the last part of the path
        path_parts = url.strip("/").split("/")
        if path_parts:
            # Use the last part of the path as the base ID
            base_id = path_parts[-1]
            # Clean the ID to be URL-friendly
            clean_id = re.sub(r'[^a-zA-Z0-9_-]', '-', base_id)
            return clean_id.lower()
        
        # Fallback to timestamp-based ID
        return f"imported-model-{int(time.time())}"
    
    @classmethod
    def _determine_mimetype(cls, file_name):
        """Determine the MIME type of a file based on its extension."""
        extension = file_name.split('.')[-1].lower()
        if extension == "bpmn":
            return "application/xml"
        elif extension == "dmn":
            return "application/xml"
        elif extension == "json":
            return "application/json"
        elif extension == "md":
            return "text/markdown"
        else:
            return "application/octet-stream"
    
    @classmethod
    def _commit_to_git(cls, process_model_id, commit_message):
        """Commit changes to Git."""
        try:
            GitService.commit(process_model_id, commit_message)
        except Exception as ex:
            current_app.logger.warning(f"Failed to commit to Git: {str(ex)}")
            # Continue even if Git commit fails


def is_valid_github_url(url):
    """Check if a URL is a valid GitHub repository URL."""
    if not url:
        return False
    
    # Basic URL validation
    if not url.startswith("https://github.com/"):
        return False
    
    # Validate URL structure: owner/repo/tree|blob/branch/path
    parts = url.split("/")
    if len(parts) < 7:
        return False
    
    # Check that the URL contains either /tree/ or /blob/
    if "/tree/" not in url and "/blob/" not in url:
        return False
    
    return True
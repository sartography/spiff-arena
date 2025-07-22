# Process Model Import API Design

This document outlines the design for the backend API endpoint that will support importing process models from GitHub URLs, including the OpenAPI (Swagger) specifications.

## API Endpoint Specification

### Import Process Model

**Endpoint:** `POST /process-models/{process_group_id}/import`

**Purpose:** Import a process model from a GitHub URL into the specified process group.

**URL Parameters:**

- `process_group_id`: ID of the process group where the imported model should be placed

**Request Body:**

```json
{
  "repository_url": "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
}
```

**Response:**

```json
{
  "process_model": {
    "id": "imported-process-model-id",
    "display_name": "Imported Process Model",
    "description": "Imported from GitHub repository",
    "primary_file_name": "main.bpmn",
    "primary_process_id": "process-id-from-bpmn",
    "files": [
      { "name": "process_model.json", "type": "json" },
      { "name": "main.bpmn", "type": "bpmn" }
    ]
  },
  "import_source": "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
}
```

**Status Codes:**

- 201: Successfully imported
- 400: Invalid request (malformed URL, invalid format)
- 404: Process group not found or GitHub repository not found
- 409: Conflict (process model ID already exists)
- 500: Server error during import

## OpenAPI Specification Updates

The following additions should be made to the `api.yml` file:

```yaml
paths:
  /process-models/{process_group_id}/import:
    post:
      tags:
        - Process Models
      summary: Import a process model from a GitHub URL
      description: Fetches process model files from a GitHub repository and imports them into the system
      operationId: process_model_import
      parameters:
        - name: process_group_id
          in: path
          description: ID of the process group to import the model into
          required: true
          schema:
            type: string
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required:
                - repository_url
              properties:
                repository_url:
                  type: string
                  description: The GitHub URL to the repository or directory containing the process model
                  example: "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
      responses:
        "201":
          description: Process model imported successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  process_model:
                    $ref: "#/components/schemas/ProcessModel"
                  import_source:
                    type: string
                    description: The source URL from which the model was imported
        "400":
          description: Invalid request (malformed URL, invalid format)
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
        "404":
          description: Process group not found or GitHub repository not found
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
        # No 409 status needed as ID conflicts are automatically resolved
        "500":
          description: Server error
          content:
            application/json:
              schema:
                $ref: "#/components/schemas/Error"
```

### Process Model Validation Endpoint

To support frontend preview functionality, we also need to add a validation endpoint:

```yaml
/process-models/{process_group_id}/validate-import:
  post:
    tags:
      - Process Models
    summary: Validate a GitHub URL for process model import
    description: Checks if a GitHub URL contains valid process model files and returns preview information
    operationId: process_model_validate_import
    parameters:
      - name: process_group_id
        in: path
        description: ID of the process group for validation context
        required: true
        schema:
          type: string
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            required:
              - repository_url
            properties:
              repository_url:
                type: string
                description: The GitHub URL to validate
                example: "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
    responses:
      "200":
        description: URL contains a valid process model
        content:
          application/json:
            schema:
              type: object
              properties:
                display_name:
                  type: string
                  description: The display name from the process model
                description:
                  type: string
                  description: The description from the process model
                primary_file_name:
                  type: string
                  description: The primary BPMN file name
                files:
                  type: array
                  items:
                    type: object
                    properties:
                      name:
                        type: string
                        description: File name
                      type:
                        type: string
                        description: File type (bpmn, json, etc.)
                suggested_id:
                  type: string
                  description: Suggested ID for the process model
      "400":
        description: Invalid URL or not a valid process model repository
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Error"
      "404":
        description: Repository or directory not found
        content:
          application/json:
            schema:
              $ref: "#/components/schemas/Error"
```

## Implementation Components

### 1. Controller Function

```python
# Function will be mapped to POST /process-models/{process_group_id}/import in the OpenAPI spec
def process_model_import(process_group_id):
    """Import a process model from a GitHub URL."""

    # Get request data
    body = request.json
    repository_url = body.get("repository_url")

    # Validate the URL
    if not repository_url or not _is_valid_github_url(repository_url):
        raise ApiError(
            "invalid_github_url",
            "The provided URL is not a valid GitHub repository URL",
            status_code=400
        )

    # Process the import
    try:
        # The service doesn't need to be instantiated if using class methods
        # but we'll keep the variable for code clarity
        process_model = ProcessModelImportService.import_from_github_url(
            repository_url,
            process_group_id
        )

        # Return the imported process model
        return {
            "process_model": process_model.serialized(),
            "import_source": repository_url
        }, 201

    except ProcessGroupNotFoundError as ex:
        raise ApiError(
            "process_group_not_found",
            f"The specified process group was not found: {str(ex)}",
            status_code=404
        )
    # No ProcessModelExistsError handling needed as IDs with conflicts are automatically renamed
    except GitHubRepositoryNotFoundError as ex:
        raise ApiError(
            "github_repository_not_found",
            f"The specified GitHub repository was not found: {str(ex)}",
            status_code=404
        )
    except InvalidProcessModelError as ex:
        raise ApiError(
            "invalid_process_model",
            f"The repository does not contain a valid process model: {str(ex)}",
            status_code=400
        )
```

### Validation Endpoint

```python
# Function will be mapped to POST /process-models/{process_group_id}/validate-import in the OpenAPI spec
def process_model_validate_import(process_group_id):
    """Validate a GitHub URL for process model import."""

    # Get request data
    body = request.json
    repository_url = body.get("repository_url")

    # Validate the URL
    if not repository_url or not _is_valid_github_url(repository_url):
        raise ApiError(
            "invalid_github_url",
            "The provided URL is not a valid GitHub repository URL",
            status_code=400
        )

    # Process validation
    try:
        # The service doesn't need to be instantiated if using class methods
        # but we'll keep the variable for code clarity
        validation_result = ProcessModelImportService.validate_github_url(repository_url)

        # Return validation result
        return validation_result, 200

    except GitHubRepositoryNotFoundError as ex:
        raise ApiError(
            "github_repository_not_found",
            f"The specified GitHub repository was not found: {str(ex)}",
            status_code=404
        )
    except InvalidProcessModelError as ex:
        raise ApiError(
            "invalid_process_model",
            f"The repository does not contain a valid process model: {str(ex)}",
            status_code=400
        )
```

### 2. ProcessModelImportService Class

```python
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
            # ID conflicts are automatically resolved by appending a timestamp
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
    def validate_github_url(cls, url):
        """Validate a GitHub URL and return preview information.

        Args:
            url: The GitHub URL to validate

        Returns:
            dict: Preview information about the process model

        Raises:
            GitHubRepositoryNotFoundError: If the GitHub repository was not found
            InvalidProcessModelError: If the repository does not contain a valid process model
        """
        # Parse GitHub URL to get repository info
        repo_info = cls._parse_github_url(url)

        # Fetch the files from GitHub
        files = cls._fetch_files_from_github(repo_info)

        # Extract process model info from files
        model_info = cls._extract_process_model_info(files)

        # Generate suggested ID from URL
        suggested_id = cls._generate_id_from_url(url)

        # Create preview response
        preview = {
            "display_name": model_info.get("display_name", suggested_id.replace("-", " ").title()),
            "description": model_info.get("description", f"Imported from {url}"),
            "primary_file_name": model_info.get("primary_file_name"),
            "suggested_id": suggested_id,
            "files": []
        }

        # Add file information
        for file_name in files.keys():
            file_type = file_name.split(".")[-1] if "." in file_name else "unknown"
            preview["files"].append({
                "name": file_name,
                "type": file_type
            })

        return preview

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
```

### 3. Custom Exceptions

```python
class ImportError(Exception):
    """Base class for import-related exceptions."""
    pass

class InvalidGitHubUrlError(ImportError):
    """Exception raised when a GitHub URL is invalid."""
    pass

class GitHubRepositoryNotFoundError(ImportError):
    """Exception raised when a GitHub repository is not found."""
    pass

class InvalidProcessModelError(ImportError):
    """Exception raised when a repository does not contain a valid process model."""
    pass

# ProcessModelExistsError no longer needed as ID conflicts are automatically resolved

class ProcessGroupNotFoundError(ImportError):
    """Exception raised when a process group is not found."""
    pass
```

## URL Validation Helper Function

```python
def _is_valid_github_url(url):
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
```

## Request and Response JSON Schema

### Import Request Schema

```json
{
  "type": "object",
  "required": ["repository_url"],
  "properties": {
    "repository_url": {
      "type": "string",
      "description": "The GitHub URL to the repository or directory containing the process model",
      "pattern": "^https://github\\.com/[^/]+/[^/]+/(tree|blob)/[^/]+/.+$"
    }
  }
}
```

### Import Response Schema

```json
{
  "type": "object",
  "required": ["process_model", "import_source"],
  "properties": {
    "process_model": {
      "type": "object",
      "required": ["id", "display_name"],
      "properties": {
        "id": {
          "type": "string"
        },
        "display_name": {
          "type": "string"
        },
        "description": {
          "type": "string"
        },
        "primary_file_name": {
          "type": "string"
        },
        "primary_process_id": {
          "type": "string"
        },
        "files": {
          "type": "array",
          "items": {
            "type": "object",
            "required": ["name", "type"],
            "properties": {
              "name": {
                "type": "string"
              },
              "type": {
                "type": "string"
              }
            }
          }
        }
      }
    },
    "import_source": {
      "type": "string"
    }
  }
}
```

### Validate Request Schema

```json
{
  "type": "object",
  "required": ["repository_url"],
  "properties": {
    "repository_url": {
      "type": "string",
      "description": "The GitHub URL to validate",
      "pattern": "^https://github\\.com/[^/]+/[^/]+/(tree|blob)/[^/]+/.+$"
    }
  }
}
```

### Validate Response Schema

```json
{
  "type": "object",
  "properties": {
    "display_name": {
      "type": "string"
    },
    "description": {
      "type": "string"
    },
    "primary_file_name": {
      "type": "string"
    },
    "suggested_id": {
      "type": "string"
    },
    "files": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": {
            "type": "string"
          },
          "type": {
            "type": "string"
          }
        }
      }
    }
  }
}
```

## Testing Strategy

1. **Unit Tests**

   - Test URL parsing for different GitHub URL formats
   - Test file fetching from GitHub with mocked responses
   - Test process model info extraction from different file sets

2. **Integration Tests**
   - Test the full import flow with actual GitHub repository in the frontend test/browser dir
   - Test error handling for various edge cases

## Security Considerations

1. Only access public GitHub repositories using the public API
2. Validate and sanitize all external content before storing
3. Ensure file size limits to prevent overloading the system


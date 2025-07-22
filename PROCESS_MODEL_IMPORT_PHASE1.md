# Process Model Import Phase 1 - Specification

## Overview

The Process Model Import feature allows users to import existing process models directly from GitHub URLs instead of creating them from scratch. This document outlines the specific implementation details for Phase 1 of this feature.

## Phase 1 Scope

Phase 1 focuses on importing process models from public GitHub repositories by providing a URL to a process model directory. The main goals are:

1. Allow users to input a GitHub URL to a process model directory
2. Fetch the files from that repository 
3. Import them into a new process model in the system
4. Handle naming conflicts appropriately

## User Experience

### Import Process Flow

1. User navigates to the process model creation area
2. User clicks "Import Process Model" option
3. User enters a GitHub URL in the provided text field
4. System validates the URL and checks that it points to a valid process model directory
5. System fetches metadata about the process model to display preview information
6. User confirms import, optionally modifying the process model ID if needed
7. System imports all files from the GitHub repository into a new process model
8. User is redirected to the newly created process model

### UI Components

1. **Import Process Model Button** - Added near the "Create Process Model" button
2. **Import Dialog** - A modal dialog containing:
   - Text field for GitHub URL input
   - Preview section showing process model details when available
   - Option to modify the process model ID
   - Import confirmation button

## Backend Implementation

### New API Endpoint

```
POST /process-models/{process_group_id}/import
```

**Request Body:**
```json
{
  "repository_url": "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example",
  "process_model_id": "optional-custom-id"
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
      {"name": "process_model.json", "type": "json"},
      {"name": "main.bpmn", "type": "bpmn"}
    ]
  },
  "import_source": "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
}
```

### Backend Service Implementation

1. **ImportService Class** - New service to handle process model imports
   - Methods:
     - `import_from_github_url(url, process_group_id, custom_id=None)`
     - `validate_github_url(url)`
     - `fetch_process_model_files(url)`
     - `create_process_model_from_files(files, process_group_id, custom_id)`

2. **GitHub URL Processing**
   - Parse GitHub URLs to extract:
     - Repository owner
     - Repository name
     - Branch name
     - Directory path within the repository
   - Support both formats:
     - `https://github.com/owner/repo/tree/branch/path/to/model`
     - `https://github.com/owner/repo/blob/branch/path/to/file`

3. **File Retrieval**
   - Use GitHub API to fetch directory contents
   - Download each file in the directory
   - Support process_model.json and BPMN files

4. **Process Model Creation**
   - Create new process model using ProcessModelService
   - Upload all retrieved files to the new model
   - Set primary file and process ID from process_model.json if available

5. **Conflict Resolution**
   - Check if process model ID already exists
   - If exists, either:
     - Use custom ID provided by user
     - Auto-generate unique ID by appending timestamp or counter
   - Return the final ID used in the response

## Frontend Implementation

### New Components

1. **ProcessModelImport.tsx** - Main import component
   - Handles URL input and validation
   - Sends import request to backend
   - Shows preview of process model when available
   - Handles import success/failure UI

2. **GithubUrlInput.tsx** - Specialized input component
   - Validates GitHub URLs
   - Provides inline feedback on URL format

3. **ProcessModelImportButton.tsx** - Button component
   - Located near the "Create Process Model" button
   - Opens the import dialog when clicked

### API Integration

1. Add `importProcessModel` function to the ProcessModelService:
```typescript
importProcessModel(
  processGroupId: string,
  repositoryUrl: string,
  customId?: string
): Promise<ProcessModel>
```

2. Implement HTTP request using HttpService:
```typescript
HttpService.makeCallToBackend({
  method: 'POST',
  url: `/process-models/${processGroupId}/import`,
  data: {
    repository_url: repositoryUrl,
    process_model_id: customId
  },
  successCallback: (processModel) => {
    // Handle success - navigate to the new model
  },
  errorCallback: (error) => {
    // Handle error - show message
  }
});
```

## Security Considerations

1. **URL Validation**
   - Only accept GitHub URLs from whitelisted domains (github.com)
   - Validate URL format before sending to backend

2. **Content Validation**
   - Validate that the imported files are valid BPMN/DMN/JSON files
   - Check for malicious content in scripts

3. **Rate Limiting**
   - Implement rate limiting for the import endpoint
   - Add timeouts for GitHub API requests

## Testing

1. **Unit Tests**
   - Test URL validation logic
   - Test process model creation from files
   - Test conflict resolution

2. **Integration Tests**
   - Test the full import flow
   - Test with various GitHub repository structures

3. **Playwright Test**
   - Verify the end-to-end import process in the browser
   - Test importing the example process model
   - Verify that the imported model works correctly

## Limitations for Phase 1

1. Only public GitHub repositories are supported
2. No support for authentication (private repositories)
3. Limited to single directory imports
4. No support for recursive imports (sub-models)
5. No automatic dependency resolution

## Future Enhancements (Post Phase 1)

1. Support for private GitHub repositories
2. Support for other Git providers (GitLab, Bitbucket)
3. Support for ZIP file uploads
4. Version tracking for imported models
5. Dependency management between imported models

## Example URLs for Testing

- Basic example: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example
- Process with form: https://github.com/sartography/example-process-models/tree/main/examples/1-0-three-step-process

## Implementation Timeline

1. Backend API endpoint and service - 3 days
2. Frontend import dialog and integration - 2 days
3. Testing and bug fixes - 2 days
4. Documentation - 1 day

Total estimated time: 8 days
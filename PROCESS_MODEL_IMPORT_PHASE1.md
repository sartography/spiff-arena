# Process Model Import Phase 1 - Specification

## Overview

The Process Model Import feature allows users to import existing process models directly from GitHub URLs instead of creating them from scratch. This document outlines the specific implementation details for Phase 1 of this feature.

## Phase 1 Scope

Phase 1 focuses on importing process models from public GitHub repositories by providing a URL to a process model directory. The main goals are:

1. Allow users to input a GitHub URL to a process model directory
2. Fetch the files from that repository 
3. Import them into a new process model in the system
4. Handle naming conflicts automatically

## User Experience

### Import Process Flow

1. User navigates to the process model creation area
2. User clicks "Import from GitHub" button
3. User enters a GitHub URL in a dialog
4. User clicks Import
5. System validates the URL, fetches files, and imports the process model
6. On success, user is redirected to the newly created process model
7. On failure, user sees an appropriate error message

### UI Components

1. **Import Process Model Button** - Added near the "Create Process Model" button
2. **Import Dialog** - A simple modal dialog containing:
   - Text field for GitHub URL input
   - Import button
   - Cancel button

## Backend Implementation

### API Endpoint

```
POST /process-models/{process_group_id}/import
```

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
      {"name": "process_model.json", "type": "json"},
      {"name": "main.bpmn", "type": "bpmn"}
    ]
  },
  "import_source": "https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
}
```

### Backend Service Implementation

1. **ProcessModelImportService Class** - Class to handle process model imports with:
   - URL validation
   - GitHub file fetching
   - Process model creation and file import
   - Automatic ID conflict resolution

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
   - Generate unique ID when conflicts occur by appending timestamp

## Frontend Implementation

### New Components

1. **ProcessModelImportButton.tsx** - Button component
   - Located near the "Create Process Model" button
   - Opens the import dialog when clicked

2. **ProcessModelImportDialog.tsx** - Simple dialog component
   - Contains field for GitHub URL input
   - Has Import and Cancel buttons
   - Displays error messages if import fails

### Integration with Process Model List

Modify the `ProcessModelList.tsx` component to include the import button and dialog.

### API Integration

```typescript
importProcessModel(processGroupId: string, repositoryUrl: string): Promise<ProcessModel> {
  return HttpService.makeCallToBackend({
    method: 'POST',
    url: `/process-models/${processGroupId}/import`,
    data: {
      repository_url: repositoryUrl
    },
    successCallback: (processModel) => {
      // Handle success - navigate to the new model
    },
    errorCallback: (error) => {
      // Handle error - show message
    }
  });
}
```

## Testing

1. **Playwright Test**
   - Create a test in `spiffworkflow-frontend/test/browser/test_process_model_import.py`
   - Test importing a process model from GitHub
   - Verify that the imported model works correctly

## Example URLs for Testing

- Basic example: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example

## Implementation Timeline

1. Backend API endpoint and service - 2 days
2. Frontend import dialog and integration - 1 day
3. Testing and bug fixes - 1 day

Total estimated time: 4 days
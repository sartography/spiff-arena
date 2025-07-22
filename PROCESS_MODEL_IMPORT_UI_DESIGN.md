# Process Model Import UI Design

This document outlines the design for the frontend UI components that will support importing process models from GitHub URLs.

## UI Components

### 1. ProcessModelImportButton Component

A button component that will be placed near the "Create Process Model" button to allow users to import process models.

```tsx
// ProcessModelImportButton.tsx
import React from 'react';
import { Button } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';

interface ProcessModelImportButtonProps {
  onClick: () => void;
}

export const ProcessModelImportButton = ({ onClick }: ProcessModelImportButtonProps) => {
  return (
    <Button
      variant="contained"
      color="primary"
      startIcon={<GitHubIcon />}
      onClick={onClick}
      data-testid="process-model-import-button"
    >
      Import from GitHub
    </Button>
  );
};
```

### 2. ProcessModelImportDialog Component

A modal dialog that will appear when the user clicks the Import button. It will contain a form for entering the GitHub URL and provide feedback on the validity of the URL.

```tsx
// ProcessModelImportDialog.tsx
import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  CircularProgress,
  Typography,
  Box,
  Alert,
  FormControl,
  InputLabel,
  InputAdornment,
  IconButton,
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import HttpService from '../services/HttpService';

interface ProcessModelImportDialogProps {
  open: boolean;
  onClose: () => void;
  processGroupId: string;
  onImportSuccess: (processModelId: string) => void;
}

export const ProcessModelImportDialog = ({
  open,
  onClose,
  processGroupId,
  onImportSuccess,
}: ProcessModelImportDialogProps) => {
  const [repositoryUrl, setRepositoryUrl] = useState('');
  // Custom ID field removed - backend will automatically handle ID generation
  const [isValidUrl, setIsValidUrl] = useState<boolean | null>(null);
  const [isValidating, setIsValidating] = useState(false);
  const [previewData, setPreviewData] = useState<any>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Validate URL when it changes
  useEffect(() => {
    const validateUrl = async () => {
      if (!repositoryUrl || repositoryUrl.length < 10) {
        setIsValidUrl(null);
        setPreviewData(null);
        return;
      }

      if (!repositoryUrl.startsWith('https://github.com/')) {
        setIsValidUrl(false);
        setPreviewData(null);
        return;
      }

      if (!/https:\/\/github\.com\/[^\/]+\/[^\/]+\/(tree|blob)\/[^\/]+\/.*/.test(repositoryUrl)) {
        setIsValidUrl(false);
        setPreviewData(null);
        return;
      }

      setIsValidating(true);
      setIsValidUrl(null);

      try {
        // Call API to validate URL and get preview data
        const result = await HttpService.makeCallToBackend({
          method: 'POST',
          url: `/process-models/${processGroupId}/validate-import`,
          data: { repository_url: repositoryUrl },
        });

        setIsValidUrl(true);
        setPreviewData(result.data);
        
        // ID generation will be handled by the backend
      } catch (error) {
        setIsValidUrl(false);
        setErrorMessage(error.response?.data?.message || 'Failed to validate URL');
      } finally {
        setIsValidating(false);
      }
    };

    // Use a debounce to avoid excessive API calls
    const timer = setTimeout(validateUrl, 500);
    return () => clearTimeout(timer);
  }, [repositoryUrl, processGroupId]);

  const handleImport = async () => {
    if (!isValidUrl) return;

    setIsImporting(true);
    setErrorMessage(null);

    try {
      const result = await HttpService.makeCallToBackend({
        method: 'POST',
        url: `/process-models/${processGroupId}/import`,
        data: {
          repository_url: repositoryUrl,
          // No custom ID - backend will handle ID generation
        },
      });

      onImportSuccess(result.data.process_model.id);
      onClose();
    } catch (error) {
      setErrorMessage(error.response?.data?.message || 'Import failed');
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Import Process Model from GitHub</DialogTitle>
      <DialogContent>
        <Box sx={{ my: 2 }}>
          <Typography variant="body1" gutterBottom>
            Enter the GitHub URL of a process model to import:
          </Typography>
          <TextField
            fullWidth
            label="GitHub Repository URL"
            variant="outlined"
            value={repositoryUrl}
            onChange={(e) => setRepositoryUrl(e.target.value)}
            placeholder="https://github.com/owner/repo/tree/branch/path/to/model"
            margin="normal"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <GitHubIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  {isValidating ? (
                    <CircularProgress size={20} />
                  ) : isValidUrl === true ? (
                    <CheckCircleIcon color="success" />
                  ) : isValidUrl === false ? (
                    <ErrorIcon color="error" />
                  ) : null}
                </InputAdornment>
              ),
            }}
            error={isValidUrl === false}
            helperText={
              isValidUrl === false
                ? "Please enter a valid GitHub URL to a process model directory"
                : "Example: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example"
            }
            disabled={isImporting}
            data-testid="repository-url-input"
          />

          {/* Custom ID field */}
          {/* Custom ID field removed - backend will automatically handle ID generation */}

          {/* Error message display */}
          {errorMessage && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {errorMessage}
            </Alert>
          )}

          {/* Preview section */}
          {previewData && (
            <Box sx={{ mt: 3, p: 2, border: 1, borderColor: 'grey.300', borderRadius: 1 }}>
              <Typography variant="h6" gutterBottom>
                Preview
              </Typography>
              <Typography variant="body2">
                <strong>Display Name:</strong> {previewData.display_name || 'N/A'}
              </Typography>
              <Typography variant="body2">
                <strong>Description:</strong> {previewData.description || 'N/A'}
              </Typography>
              <Typography variant="body2">
                <strong>Primary File:</strong> {previewData.primary_file_name || 'N/A'}
              </Typography>
              <Typography variant="body2">
                <strong>Files:</strong> {previewData.files?.length || 0} files found
              </Typography>
            </Box>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={isImporting}>
          Cancel
        </Button>
        <Button
          onClick={handleImport}
          variant="contained"
          color="primary"
          disabled={!isValidUrl || isImporting}
          startIcon={isImporting ? <CircularProgress size={20} /> : <GitHubIcon />}
          data-testid="import-button"
        >
          {isImporting ? 'Importing...' : 'Import Model'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

### 3. Integration with Process Model List Page

Modify the `ProcessModelList.tsx` component to include the import button and dialog:

```tsx
// ProcessModelList.tsx (partial example of modifications)
import React, { useState } from 'react';
// ... existing imports
import { ProcessModelImportButton } from '../components/ProcessModelImportButton';
import { ProcessModelImportDialog } from '../components/ProcessModelImportDialog';

export const ProcessModelList = () => {
  // ... existing state and hooks
  const [importDialogOpen, setImportDialogOpen] = useState(false);

  const handleImportSuccess = (processModelId: string) => {
    // Refresh the process model list
    refreshProcessModels();
    
    // Optional: Navigate to the imported process model
    if (processModelId) {
      navigate(`/process-models/${processModelId}`);
    }
  };

  return (
    <div>
      {/* Existing components */}
      
      {/* Add Import button next to Create button */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        {/* Existing Create Process Model button */}
        <Button
          variant="contained"
          color="primary"
          startIcon={<AddIcon />}
          component={Link}
          to={`/process-groups/${processGroupId}/process-models/new`}
          data-testid="create-process-model-button"
        >
          Create Process Model
        </Button>
        
        {/* Add Import button */}
        <ProcessModelImportButton 
          onClick={() => setImportDialogOpen(true)} 
        />
      </Box>
      
      {/* Process Model Import Dialog */}
      <ProcessModelImportDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        processGroupId={processGroupId}
        onImportSuccess={handleImportSuccess}
      />
      
      {/* Rest of existing components */}
    </div>
  );
};
```

## URL Validation API

To support the frontend's ability to preview process models before importing, we'll need an additional API endpoint:

```typescript
// HttpService call to validate import URL
const validateImportUrl = async (processGroupId: string, repositoryUrl: string) => {
  return HttpService.makeCallToBackend({
    method: 'POST',
    url: `/process-models/${processGroupId}/validate-import`,
    data: {
      repository_url: repositoryUrl
    }
  });
};
```

This endpoint will:
1. Validate that the URL is properly formatted
2. Check that it points to a valid process model directory
3. Fetch basic metadata about the process model
4. Return preview data without actually importing

## Error Handling

The UI will handle various error scenarios:

1. **Invalid URL Format**: Show an immediate validation error
2. **Repository Not Found**: Display error message from the API
3. **Invalid Process Model**: Explain what's missing or incorrect
4. **Import Failures**: Show detailed error message from the backend
5. **Conflict Resolution**: Provide guidance when ID already exists

## Testing Strategy

1. **Unit Tests**:
   - Test URL validation logic
   - Test UI state transitions
   - Test dialog open/close behavior

2. **Integration Tests**:
   - Test the interaction between components
   - Test API calls with mocked responses

3. **End-to-End Tests**:
   - Test the complete import flow
   - Verify navigation after successful import

## User Flow Diagram

```
User Flow:

1. User navigates to Process Model List
   │
2. User clicks "Import from GitHub" button
   │
3. Import Dialog opens
   │
4. User enters GitHub URL
   │     │
   │     ├── URL is invalid ──> Show validation error
   │     │
5. URL is valid, show preview data
   │
   │
7. User clicks "Import Model"
   │     │
   │     ├── Import fails ──> Show error message
   │     │
8. Import succeeds
   │
9. Close dialog and navigate to new process model
```

## Implementation Notes

1. The UI should provide immediate feedback on URL format validity
2. The preview section should only appear when the URL is valid
3. The import button should be disabled until the URL is validated
4. Show loading indicators during validation and import operations
5. Provide clear error messages when things go wrong
6. Allow the user to cancel the operation at any point
7. Ensure accessibility with proper keyboard navigation and ARIA attributes
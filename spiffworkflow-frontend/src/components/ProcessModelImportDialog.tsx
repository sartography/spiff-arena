import React, { useState } from 'react';
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
  InputAdornment,
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import HttpService from '../services/HttpService';

interface ProcessModelImportDialogProps {
  open: boolean;
  onClose: () => void;
  processGroupId: string;
  onImportSuccess: (processModelId: string) => void;
}

export function ProcessModelImportDialog({
  open,
  onClose,
  processGroupId,
  onImportSuccess,
}: ProcessModelImportDialogProps) {
  const [repositoryUrl, setRepositoryUrl] = useState('');
  const [isValidUrl, setIsValidUrl] = useState<boolean | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Validate URL when it changes
  const validateGithubUrl = (url: string): boolean => {
    // Basic URL validation
    if (!url || !url.startsWith('https://github.com/')) {
      return false;
    }

    // Validate URL structure: owner/repo/tree|blob/branch/path
    const parts = url.split('/');
    if (parts.length < 7) {
      return false;
    }

    // Check that the URL contains either /tree/ or /blob/
    return url.indexOf('/tree/') !== -1 || url.indexOf('/blob/') !== -1;
  };

  const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const url = e.target.value;
    setRepositoryUrl(url);
    if (!url || url.length < 10) {
      setIsValidUrl(null);
    } else {
      setIsValidUrl(validateGithubUrl(url));
    }
  };

  const handleImport = async () => {
    if (!isValidUrl) {
      return;
    }

    setIsImporting(true);
    setErrorMessage(null);

    try {
      const result = await HttpService.makeCallToBackend({
        method: 'POST',
        url: `/process-models/${processGroupId}/import`,
        data: {
          repository_url: repositoryUrl,
        },
      });

      onImportSuccess(result.data.process_model.id);
      onClose();
    } catch (error: any) {
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
            onChange={handleUrlChange}
            placeholder="https://github.com/owner/repo/tree/branch/path/to/model"
            margin="normal"
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <GitHubIcon />
                </InputAdornment>
              ),
            }}
            error={isValidUrl === false}
            helperText={
              isValidUrl === false
                ? 'Please enter a valid GitHub URL to a process model directory'
                : 'Example: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example'
            }
            disabled={isImporting}
            data-testid="repository-url-input"
          />

          {/* Error message display */}
          {errorMessage && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {errorMessage}
            </Alert>
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
          startIcon={
            isImporting ? <CircularProgress size={20} /> : <GitHubIcon />
          }
          data-testid="import-button"
        >
          {isImporting ? 'Importing...' : 'Import Model'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

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
  Tabs,
  Tab,
} from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';
import TagIcon from '@mui/icons-material/LocalOffer';
import DownloadIcon from '@mui/icons-material/Download';
import HttpService from '../services/HttpService';
import { ProcessModel } from '../interfaces';

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
  const [importSource, setImportSource] = useState('');
  const [isValid, setIsValid] = useState<boolean | null>(null);
  const [isImporting, setIsImporting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [importType, setImportType] = useState<'github' | 'marketplace'>('github');

  // Validate input based on selected import type
  const validateInput = (value: string): boolean => {
    if (importType === 'github') {
      return validateGithubUrl(value);
    } else {
      return validateModelAlias(value);
    }
  };

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
  
  const validateModelAlias = (alias: string): boolean => {
    // Model alias should be a simple string with only alphanumeric characters, hyphens, and underscores
    return /^[a-zA-Z0-9_-]+$/.test(alias);
  };

  const handleSourceChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setImportSource(value);
    if (!value || value.length < 3) {
      setIsValid(null);
    } else {
      setIsValid(validateInput(value));
    }
  };
  
  const handleTabChange = (_event: React.SyntheticEvent, newValue: 'github' | 'marketplace') => {
    setImportType(newValue);
    setImportSource('');
    setIsValid(null);
  };

  const handleImport = async () => {
    if (!isValid) {
      return;
    }

    setIsImporting(true);
    setErrorMessage(null);

    try {
      console.log('Importing from source:', importSource);
      console.log('Process Group ID:', processGroupId);

      HttpService.makeCallToBackend({
        httpMethod: 'POST',
        path: `/process-model-import/${processGroupId}`,
        postBody: {
          repository_url: importSource,
        },
        successCallback: (result: { process_model: ProcessModel }) => {
          console.log('Import API success response:', JSON.stringify(result));

          if (result && result.process_model && result.process_model.id) {
            const processModelId = result.process_model.id;
            console.log(
              'Successfully imported process model with ID:',
              processModelId,
            );
            onImportSuccess(processModelId);
          } else {
            console.error(
              'Import response missing expected data structure:',
              result,
            );
            // Call with empty string if ID not available
            console.log('Calling onImportSuccess with empty string');
            onImportSuccess('');
          }
          onClose();
        },
        failureCallback: (error: any) => {
          console.error('Import error:', error);
          setErrorMessage(error?.message || 'Import failed');
        },
      });
    } finally {
      setIsImporting(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Import Process Model</DialogTitle>
      <DialogContent>
        <Box sx={{ width: '100%', mb: 2 }}>
          <Tabs
            value={importType}
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab 
              value="github" 
              label="GitHub Repository" 
              icon={<GitHubIcon />}
              iconPosition="start"
            />
            <Tab 
              value="marketplace" 
              label="Model Marketplace" 
              icon={<TagIcon />}
              iconPosition="start"
            />
          </Tabs>
        </Box>
        <Box sx={{ my: 2 }}>
          {importType === 'github' ? (
            <>
              <Typography variant="body1" gutterBottom>
                Enter the GitHub URL of a process model to import:
              </Typography>
              <TextField
                fullWidth
                label="GitHub Repository URL"
                variant="outlined"
                value={importSource}
                onChange={handleSourceChange}
                placeholder="https://github.com/owner/repo/tree/branch/path/to/model"
                margin="normal"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <GitHubIcon />
                    </InputAdornment>
                  ),
                }}
                error={isValid === false}
                helperText={
                  isValid === false
                    ? 'Please enter a valid GitHub URL to a process model directory'
                    : 'Example: https://github.com/sartography/example-process-models/tree/main/examples/0-1-minimal-example'
                }
                disabled={isImporting}
                data-testid="repository-url-input"
              />
            </>
          ) : (
            <>
              <Typography variant="body1" gutterBottom>
                Enter the model alias to import from the marketplace:
              </Typography>
              <TextField
                fullWidth
                label="Model Alias"
                variant="outlined"
                value={importSource}
                onChange={handleSourceChange}
                placeholder="timer-events"
                margin="normal"
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <TagIcon />
                    </InputAdornment>
                  ),
                }}
                error={isValid === false}
                helperText={
                  isValid === false
                    ? 'Please enter a valid model alias (only letters, numbers, hyphens, and underscores)'
                    : 'Example: timer-events'
                }
                disabled={isImporting}
                data-testid="model-alias-input"
              />
            </>
          )}

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
          disabled={!isValid || isImporting}
          startIcon={
            isImporting ? <CircularProgress size={20} /> : <DownloadIcon />
          }
          data-testid="import-button"
        >
          {isImporting ? 'Importing...' : 'Import Model'}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

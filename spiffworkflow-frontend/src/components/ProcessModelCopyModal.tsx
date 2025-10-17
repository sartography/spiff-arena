import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Stack,
} from '@mui/material';
import { ProcessModel } from '../interfaces';

interface ProcessModelCopyModalProps {
  showCopyModal: boolean;
  processModel: ProcessModel;
  handleCopyCancel: () => void;
  handleCopyConfirm: (id: string, displayName?: string) => void;
}

export default function ProcessModelCopyModal({
  showCopyModal,
  processModel,
  handleCopyCancel,
  handleCopyConfirm,
}: ProcessModelCopyModalProps) {
  const { t } = useTranslation();
  const [newId, setNewId] = useState<string>('');
  const [newDisplayName, setNewDisplayName] = useState<string>('');
  const [validationError, setValidationError] = useState<string>('');

  const validateInputs = (): boolean => {
    if (!newId.trim()) {
      setValidationError(t('process_model_id_required'));
      return false;
    }
    // Check if process group is specified (must contain at least one forward slash)
    if (!newId.trim().includes('/')) {
      setValidationError(t('process_model_copy_group_required_error'));
      return false;
    }
    // Basic ID validation - should not contain spaces or most special characters
    if (!/^[a-zA-Z0-9_/-]+$/.test(newId.trim())) {
      setValidationError(t('process_model_id_validation_error'));
      return false;
    }
    setValidationError('');
    return true;
  };

  const handleConfirm = () => {
    if (validateInputs()) {
      handleCopyConfirm(newId.trim(), newDisplayName.trim() || undefined);
      // Clear form
      setNewId('');
      setNewDisplayName('');
      setValidationError('');
    }
  };

  const handleCancel = () => {
    handleCopyCancel();
    // Clear form
    setNewId('');
    setNewDisplayName('');
    setValidationError('');
  };

  return (
    <Dialog
      open={showCopyModal}
      onClose={handleCancel}
      aria-labelledby="copy-dialog-title"
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle id="copy-dialog-title">
        {t('copy_process_model')}
      </DialogTitle>
      <DialogContent>
        <Stack spacing={2} sx={{ mt: 1 }}>
          <Typography variant="body2" color="text.secondary">
            Copy &quot;{processModel.display_name}&quot; to a new process model
          </Typography>

          <TextField
            label="New Process Model ID"
            value={newId}
            onChange={(e) => setNewId(e.target.value)}
            placeholder="e.g., group/my-new-process-model"
            fullWidth
            required
            helperText="ID can contain letters, numbers, hyphens, underscores, and forward slashes"
          />

          <TextField
            label="Display Name"
            value={newDisplayName}
            onChange={(e) => setNewDisplayName(e.target.value)}
            placeholder="e.g., My New Process Model"
            fullWidth
            helperText={t('process_model_display_name_help_optional')}
          />

          {validationError && (
            <Typography variant="body2" color="error">
              {validationError}
            </Typography>
          )}
        </Stack>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleCancel} color="primary">
          {t('cancel')}
        </Button>
        <Button
          onClick={handleConfirm}
          color="primary"
          variant="contained"
          disabled={!newId.trim()}
        >
          {t('copy')}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

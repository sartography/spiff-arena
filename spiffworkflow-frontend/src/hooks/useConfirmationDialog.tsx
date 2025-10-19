import { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from '@mui/material';
import { useTranslation } from 'react-i18next';

interface UseConfirmationDialogOptions {
  title?: string;
  description?: string;
  confirmText?: string;
  cancelText?: string;
  confirmColor?: 'inherit' | 'primary' | 'secondary' | 'success' | 'error' | 'info' | 'warning';
}

export function useConfirmationDialog(
  onConfirm: () => void,
  options: UseConfirmationDialogOptions = {}
) {
  const { t } = useTranslation();
  const [isOpen, setIsOpen] = useState(false);

  const {
    title = t('are_you_sure'),
    description,
    confirmText = t('confirm'),
    cancelText = t('cancel'),
    confirmColor = 'error',
  } = options;

  const openDialog = () => setIsOpen(true);
  const closeDialog = () => setIsOpen(false);

  const handleConfirm = () => {
    closeDialog();
    onConfirm();
  };

  const ConfirmationDialog = () => (
    <Dialog
      open={isOpen}
      onClose={closeDialog}
      aria-labelledby="confirmation-dialog-title"
      aria-describedby="confirmation-dialog-description"
    >
      <DialogTitle id="confirmation-dialog-title">
        {title}
      </DialogTitle>
      {description && (
        <DialogContent>
          <DialogContentText id="confirmation-dialog-description">
            {description}
          </DialogContentText>
        </DialogContent>
      )}
      <DialogActions>
        <Button onClick={closeDialog} color="primary">
          {cancelText}
        </Button>
        <Button
          onClick={handleConfirm}
          color={confirmColor}
          variant="contained"
        >
          {confirmText}
        </Button>
      </DialogActions>
    </Dialog>
  );

  return {
    openConfirmation: openDialog,
    closeConfirmation: closeDialog,
    ConfirmationDialog,
    isConfirmationOpen: isOpen,
  };
}
import React from 'react';
import { Button, ButtonGroup, TextField, Box } from '@mui/material';
import DialogShell from './DialogShell';

type FileNameEditorDialogProps = {
  open: boolean;
  title: string;
  label: string;
  value: string;
  fileExtension?: string;
  errorText?: string;
  onChange: (value: string) => void;
  onSave: (event?: any) => void;
  onCancel: () => void;
  saveLabel: string;
  cancelLabel: string;
};

export default function FileNameEditorDialog({
  open,
  title,
  label,
  value,
  fileExtension,
  errorText,
  onChange,
  onSave,
  onCancel,
  saveLabel,
  cancelLabel,
}: FileNameEditorDialogProps) {
  return (
    <DialogShell
      open={open}
      onClose={onCancel}
      title={title}
      className=""
    >
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Box sx={{ flex: 2 }}>
          <TextField
            id="process_model_file_name"
            label={label}
            value={value}
            onChange={(event) => onChange(event.target.value)}
            error={!!errorText}
            helperText={errorText}
            size="small"
            autoFocus
            fullWidth
          />
        </Box>
        <Box sx={{ flex: 1, display: 'flex', alignItems: 'center' }}>{fileExtension}</Box>
      </Box>
      <ButtonGroup>
        <Button onClick={onSave}>{saveLabel}</Button>
        <Button onClick={onCancel}>{cancelLabel}</Button>
      </ButtonGroup>
    </DialogShell>
  );
}

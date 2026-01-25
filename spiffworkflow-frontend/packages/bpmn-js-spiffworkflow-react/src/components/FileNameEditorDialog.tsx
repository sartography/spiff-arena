import React from 'react';
import { Button, ButtonGroup, TextField } from '@mui/material';
import Grid from '@mui/material/Grid';
import DialogShell from './DialogShell';

type FileNameEditorDialogProps = {
  open: boolean;
  title: string;
  label: string;
  value: string;
  fileExtension?: string;
  errorText?: string;
  onChange: (value: string) => void;
  onSave: () => void;
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
      <Grid container spacing={2}>
        <Grid size={{ xs: 8 }}>
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
        </Grid>
        <Grid size={{ xs: 4 }}>{fileExtension}</Grid>
      </Grid>
      <ButtonGroup>
        <Button onClick={onSave}>{saveLabel}</Button>
        <Button onClick={onCancel}>{cancelLabel}</Button>
      </ButtonGroup>
    </DialogShell>
  );
}

import React, { ReactNode } from 'react';
import { Box, Button, Dialog } from '@mui/material';

type MessageEditorDialogProps = {
  open: boolean;
  onClose: () => void;
  onSave: (event?: any) => void;
  title: string;
  description?: string;
  saveLabel: string;
  closeLabel: string;
  renderEditor: () => ReactNode;
};

export default function MessageEditorDialog({
  open,
  onClose,
  onSave,
  title,
  description,
  saveLabel,
  closeLabel,
  renderEditor,
}: MessageEditorDialogProps) {
  if (!open) {
    return null;
  }

  return (
    <Dialog
      className="bpmn-editor-wide-dialog"
      open={open}
      onClose={onClose}
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description"
    >
      <Box sx={{ p: 4 }}>
        <h2 id="modal-modal-title">{title}</h2>
        {description ? <p id="modal-modal-description">{description}</p> : null}
        <div data-color-mode="light">{renderEditor()}</div>
        <Button onClick={onSave}>{saveLabel}</Button>
        <Button onClick={onClose}>{closeLabel}</Button>
      </Box>
    </Dialog>
  );
}

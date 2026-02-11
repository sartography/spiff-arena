import React, { ReactNode } from 'react';
import { Box, Button, Dialog } from '@mui/material';

type JsonSchemaEditorDialogProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  closeLabel: string;
  renderEditor: () => ReactNode;
};

export default function JsonSchemaEditorDialog({
  open,
  onClose,
  title,
  closeLabel,
  renderEditor,
}: JsonSchemaEditorDialogProps) {
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
        {renderEditor()}
        <Button onClick={onClose}>{closeLabel}</Button>
      </Box>
    </Dialog>
  );
}

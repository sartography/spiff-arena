import React, { ReactNode } from 'react';
import { Box, Button, Dialog } from '@mui/material';

type MarkdownEditorDialogProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  closeLabel: string;
  renderEditor: () => ReactNode;
};

export default function MarkdownEditorDialog({
  open,
  onClose,
  title,
  closeLabel,
  renderEditor,
}: MarkdownEditorDialogProps) {
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
        <div data-color-mode="light">{renderEditor()}</div>
        <Button onClick={onClose}>{closeLabel}</Button>
      </Box>
    </Dialog>
  );
}

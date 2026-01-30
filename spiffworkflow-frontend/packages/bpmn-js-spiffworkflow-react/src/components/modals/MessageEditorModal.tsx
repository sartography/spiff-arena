import React from 'react';
import { Dialog, Box, Button } from '@mui/material';

export interface MessageEditorModalProps {
  isOpen: boolean;
  messageId: string;
  elementId: string;
  correlationProperties: any;
  event: any;
  onClose: () => void;
  onSave: () => void;
  /** Custom message editor component */
  children?: React.ReactNode;
}

export function MessageEditorModal({
  isOpen,
  messageId,
  elementId,
  correlationProperties,
  event,
  onClose,
  onSave,
  children,
}: MessageEditorModalProps) {
  if (!isOpen) {
    return null;
  }

  // If custom children provided, use those (for app-specific MessageEditor)
  if (children) {
    return (
      <Dialog
        className="bpmn-editor-wide-dialog"
        open={isOpen}
        onClose={onClose}
        aria-labelledby="message-editor-title"
        maxWidth="lg"
        fullWidth
      >
        <Box sx={{ p: 4 }}>
          <h2 id="message-editor-title">Edit Message</h2>
          {children}
          <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
            <Button onClick={onSave} variant="contained" color="primary">
              Save
            </Button>
            <Button onClick={onClose} variant="outlined">
              Close
            </Button>
          </Box>
        </Box>
      </Dialog>
    );
  }

  // Simple default implementation
  return (
    <Dialog
      className="bpmn-editor-wide-dialog"
      open={isOpen}
      onClose={onClose}
      aria-labelledby="message-editor-title"
      maxWidth="md"
      fullWidth
    >
      <Box sx={{ p: 4 }}>
        <h2 id="message-editor-title">Edit Message</h2>
        <Box sx={{ mt: 2, mb: 2 }}>
          <p><strong>Message ID:</strong> {messageId}</p>
          <p><strong>Element ID:</strong> {elementId}</p>
        </Box>
        <Box sx={{ p: 3, bgcolor: '#f5f5f5', borderRadius: 1, mb: 2 }}>
          <p style={{ margin: 0, color: '#666' }}>
            <strong>Note:</strong> This is a simplified message editor.
            Provide a custom message editor component via the children prop
            for full message editing functionality.
          </p>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 1 }}>
          <Button onClick={onSave} variant="contained" color="primary">
            Save
          </Button>
          <Button onClick={onClose} variant="outlined">
            Close
          </Button>
        </Box>
      </Box>
    </Dialog>
  );
}

export default MessageEditorModal;

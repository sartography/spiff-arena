import React from 'react';
import { Dialog, Box, TextField, Button } from '@mui/material';

export interface JsonSchemaEditorModalProps {
  isOpen: boolean;
  fileName: string;
  onClose: () => void;
  onFileNameChange: (fileName: string) => void;
  /** Optional custom form builder component */
  children?: React.ReactNode;
}

export function JsonSchemaEditorModal({
  isOpen,
  fileName,
  onClose,
  onFileNameChange,
  children,
}: JsonSchemaEditorModalProps) {
  if (!isOpen) {
    return null;
  }

  // If custom children provided, use those (for ReactFormBuilder integration)
  if (children) {
    return (
      <Dialog
        className="bpmn-editor-wide-dialog"
        open={isOpen}
        onClose={onClose}
        aria-labelledby="json-schema-editor-title"
        maxWidth="lg"
        fullWidth
      >
        {children}
      </Dialog>
    );
  }

  // Otherwise provide simple default implementation
  return (
    <Dialog
      className="bpmn-editor-wide-dialog"
      open={isOpen}
      onClose={onClose}
      aria-labelledby="json-schema-editor-title"
      maxWidth="lg"
      fullWidth
    >
      <Box sx={{ p: 4 }}>
        <h2 id="json-schema-editor-title">Edit JSON Schema</h2>
        <Box sx={{ mt: 2, mb: 3 }}>
          <TextField
            fullWidth
            label="File Name"
            value={fileName}
            onChange={(e) => onFileNameChange(e.target.value)}
            placeholder="schema-file.json"
            helperText="Enter the name for the JSON schema file"
          />
        </Box>
        <Box sx={{ p: 3, bgcolor: '#f5f5f5', borderRadius: 1, mb: 2 }}>
          <p style={{ margin: 0, color: '#666' }}>
            <strong>Note:</strong> This is a simplified JSON schema editor. For
            full form building functionality, provide a custom editor via the
            children prop or integrate with a form builder like
            ReactFormBuilder.
          </p>
        </Box>
        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} variant="contained">
            Close
          </Button>
        </Box>
      </Box>
    </Dialog>
  );
}

export default JsonSchemaEditorModal;

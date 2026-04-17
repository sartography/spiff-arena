import React from 'react';
import { Dialog, Box, Button, TextareaAutosize } from '@mui/material';
import MDEditor from '@uiw/react-md-editor';

export interface MarkdownEditorModalProps {
  isOpen: boolean;
  markdown: string;
  onClose: () => void;
  onMarkdownChange: (markdown?: string) => void;
}

export function MarkdownEditorModal({
  isOpen,
  markdown,
  onClose,
  onMarkdownChange,
}: MarkdownEditorModalProps) {
  const markdownEditorTextArea = (props: any) => {
    return <TextareaAutosize {...props} />;
  };

  if (!isOpen) {
    return null;
  }

  return (
    <Dialog
      className="bpmn-editor-wide-dialog"
      open={isOpen}
      onClose={onClose}
      aria-labelledby="markdown-editor-title"
      maxWidth="lg"
      fullWidth
    >
      <Box sx={{ p: 4 }}>
        <h2 id="markdown-editor-title">Edit Markdown</h2>
        <div data-color-mode="light">
          <MDEditor
            height={500}
            highlightEnable={false}
            value={markdown}
            onChange={onMarkdownChange}
            components={{
              textarea: markdownEditorTextArea,
            }}
          />
        </div>
        <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
          <Button onClick={onClose} variant="contained">Close</Button>
        </Box>
      </Box>
    </Dialog>
  );
}

export default MarkdownEditorModal;

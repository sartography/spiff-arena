import React from 'react';
import { Dialog, Box } from '@mui/material';
import type { ProcessReference } from '../../hooks/useBpmnEditorModals';

export interface ProcessSearchModalProps {
  isOpen: boolean;
  processes: ProcessReference[];
  onClose: (selection?: ProcessReference | null) => void;
  /** Optional custom process search component */
  children?: React.ReactNode;
}

export function ProcessSearchModal({
  isOpen,
  processes,
  onClose,
  children,
}: ProcessSearchModalProps) {
  if (!isOpen) {
    return null;
  }

  // If custom children provided, use those
  if (children) {
    return (
      <Dialog
        className="bpmn-editor-wide-dialog"
        open={isOpen}
        onClose={() => onClose(null)}
        maxWidth="md"
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
      onClose={() => onClose(null)}
      aria-labelledby="process-search-title"
      maxWidth="md"
      fullWidth
    >
      <Box sx={{ p: 4 }}>
        <h2 id="process-search-title">Select Process</h2>
        <Box sx={{ mt: 2, maxHeight: '500px', overflowY: 'auto' }}>
          {processes.length === 0 ? (
            <p>No processes available</p>
          ) : (
            <ul style={{ listStyle: 'none', padding: 0 }}>
              {processes.map((process) => (
                <li
                  key={process.identifier}
                  style={{
                    padding: '12px',
                    marginBottom: '8px',
                    backgroundColor: '#f5f5f5',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    transition: 'background-color 0.2s',
                  }}
                  onClick={() => onClose(process)}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.backgroundColor = '#e0e0e0';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.backgroundColor = '#f5f5f5';
                  }}
                >
                  <strong>{process.display_name}</strong>
                  <br />
                  <small style={{ color: '#666' }}>{process.identifier}</small>
                </li>
              ))}
            </ul>
          )}
        </Box>
      </Box>
    </Dialog>
  );
}

export default ProcessSearchModal;

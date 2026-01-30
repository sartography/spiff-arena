import React, { ReactNode } from 'react';
import { Box, Dialog } from '@mui/material';

type DialogShellProps = {
  open: boolean;
  onClose: () => void;
  title?: string;
  titleId?: string;
  descriptionId?: string;
  className?: string;
  children: ReactNode;
  footer?: ReactNode;
};

export default function DialogShell({
  open,
  onClose,
  title,
  titleId = 'modal-modal-title',
  descriptionId,
  className = 'bpmn-editor-wide-dialog',
  children,
  footer,
}: DialogShellProps) {
  if (!open) {
    return null;
  }

  return (
    <Dialog
      className={className}
      open={open}
      onClose={onClose}
      aria-labelledby={titleId}
      {...(descriptionId && { 'aria-describedby': descriptionId })}
    >
      <Box sx={{ p: 4 }}>
        {title ? <h2 id={titleId}>{title}</h2> : null}
        {children}
        {footer || null}
      </Box>
    </Dialog>
  );
}

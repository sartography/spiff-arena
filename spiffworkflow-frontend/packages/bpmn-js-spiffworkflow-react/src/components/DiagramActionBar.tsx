import React, { ReactNode } from 'react';
import { Button, Stack } from '@mui/material';

type DiagramActionBarProps = {
  canSave?: boolean;
  onSave?: () => void;
  saveDisabled?: boolean;
  saveLabel: string;
  canDelete?: boolean;
  onDelete?: () => void;
  deleteLabel?: string;
  deleteDescription?: ReactNode;
  deleteButton?: ReactNode;
  canSetPrimary?: boolean;
  onSetPrimary?: () => void;
  setPrimaryLabel: string;
  canDownload?: boolean;
  onDownload?: () => void;
  downloadLabel: string;
  canViewXml?: boolean;
  onViewXml?: () => void;
  viewXmlLabel: string;
  referencesButton?: ReactNode;
  processInstanceRun?: ReactNode;
  activeUserElement?: ReactNode;
};

export default function DiagramActionBar({
  canSave,
  onSave,
  saveDisabled,
  saveLabel,
  canDelete,
  onDelete,
  deleteLabel,
  deleteDescription,
  deleteButton,
  canSetPrimary,
  onSetPrimary,
  setPrimaryLabel,
  canDownload,
  onDownload,
  downloadLabel,
  canViewXml,
  onViewXml,
  viewXmlLabel,
  referencesButton,
  processInstanceRun,
  activeUserElement,
}: DiagramActionBarProps) {
  return (
    <Stack sx={{ mt: 2 }} direction="row" spacing={2}>
      {canSave && onSave ? (
        <Button
          onClick={onSave}
          variant="contained"
          disabled={saveDisabled}
          data-testid="process-model-file-save-button"
        >
          {saveLabel}
        </Button>
      ) : null}
      {processInstanceRun || null}
      {canDelete ? deleteButton || null : null}
      {canSetPrimary && onSetPrimary ? (
        <Button onClick={onSetPrimary} variant="contained">
          {setPrimaryLabel}
        </Button>
      ) : null}
      {canDownload && onDownload ? (
        <Button variant="contained" onClick={onDownload}>
          {downloadLabel}
        </Button>
      ) : null}
      {canViewXml && onViewXml ? (
        <Button variant="contained" onClick={onViewXml}>
          {viewXmlLabel}
        </Button>
      ) : null}
      {referencesButton || null}
      {activeUserElement || null}
    </Stack>
  );
}

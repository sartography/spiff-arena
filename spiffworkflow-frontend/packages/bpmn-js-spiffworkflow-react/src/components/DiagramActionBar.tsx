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
  downloadLabel?: string;
  canViewXml?: boolean;
  onViewXml?: () => void;
  viewXmlLabel?: string;
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
    <Stack
      className="diagram-action-bar"
      direction="row"
      spacing={1.5}
      alignItems="center"
      sx={{ flexWrap: 'wrap' }}
    >
      {canSave && onSave ? (
        <Button
          onClick={onSave}
          variant="contained"
          size="small"
          disabled={saveDisabled}
          data-testid="process-model-file-save-button"
        >
          {saveLabel}
        </Button>
      ) : null}
      {processInstanceRun || null}
      {canDelete ? deleteButton || null : null}
      {canSetPrimary && onSetPrimary ? (
        <Button onClick={onSetPrimary} variant="outlined" size="small">
          {setPrimaryLabel}
        </Button>
      ) : null}
      {canDownload && onDownload ? (
        <Button variant="outlined" size="small" onClick={onDownload}>
          {downloadLabel}
        </Button>
      ) : null}
      {canViewXml && onViewXml ? (
        <Button variant="outlined" size="small" onClick={onViewXml}>
          {viewXmlLabel}
        </Button>
      ) : null}
      {referencesButton || null}
      {activeUserElement || null}
    </Stack>
  );
}

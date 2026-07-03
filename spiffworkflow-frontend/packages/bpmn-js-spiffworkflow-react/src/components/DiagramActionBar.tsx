import React, { ReactNode } from 'react';
import { Button, Stack, Typography } from '@mui/material';
import { WarningAmber } from '@mui/icons-material';

type DiagramActionBarProps = {
  canSave?: boolean;
  onSave?: () => void;
  saveDisabled?: boolean;
  saveLabel: string;
  saveRequiresAttention?: boolean;
  saveTooltip?: ReactNode;
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
  saveRequiresAttention,
  saveTooltip,
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
  const shouldShowSaveAttention = saveRequiresAttention && !saveDisabled;

  const saveButton = canSave && onSave ? (
    <Button
      onClick={onSave}
      variant="contained"
      size="small"
      color="primary"
      disabled={saveDisabled}
      data-testid="process-model-file-save-button"
    >
      {saveLabel}
    </Button>
  ) : null;

  const saveAttentionMessage =
    shouldShowSaveAttention && saveTooltip ? (
      <Stack
        direction="row"
        spacing={0.5}
        alignItems="center"
        role="status"
        aria-live="polite"
        data-testid="process-model-file-unsaved-message"
        sx={{
          color: 'warning.dark',
          minHeight: 30,
          maxWidth: { xs: '100%', md: 380 },
        }}
      >
        <WarningAmber fontSize="small" />
        <Typography
          component="span"
          variant="body2"
          sx={{ fontWeight: 700, lineHeight: 1.25 }}
        >
          {saveTooltip}
        </Typography>
      </Stack>
    ) : null;

  return (
    <Stack
      className="diagram-action-bar"
      direction="row"
      spacing={1.5}
      alignItems="center"
      sx={{ flexWrap: 'wrap' }}
    >
      {saveAttentionMessage}
      {saveButton}
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

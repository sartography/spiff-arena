import React from 'react';
import { Button } from '@mui/material';
import DownloadIcon from '@mui/icons-material/Download';

interface ProcessModelImportButtonProps {
  onClick: () => void;
}

export function ProcessModelImportButton({
  onClick,
}: ProcessModelImportButtonProps) {
  return (
    <Button
      variant="contained"
      color="primary"
      startIcon={<DownloadIcon />}
      onClick={onClick}
      data-testid="process-model-import-button"
    >
      Import Process Model
    </Button>
  );
}

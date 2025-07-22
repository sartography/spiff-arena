import React from 'react';
import { Button } from '@mui/material';
import GitHubIcon from '@mui/icons-material/GitHub';

interface ProcessModelImportButtonProps {
  onClick: () => void;
}

export const ProcessModelImportButton = ({ onClick }: ProcessModelImportButtonProps) => {
  return (
    <Button
      variant="contained"
      color="primary"
      startIcon={<GitHubIcon />}
      onClick={onClick}
      data-testid="process-model-import-button"
    >
      Import from GitHub
    </Button>
  );
};
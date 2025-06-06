import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import Button from '@mui/material/Button';
import Dialog from '@mui/material/Dialog';
import DialogActions from '@mui/material/DialogActions';
import DialogContent from '@mui/material/DialogContent';
import DialogContentText from '@mui/material/DialogContentText';
import DialogTitle from '@mui/material/DialogTitle';
import { IconButton } from '@mui/material';
import SpiffTooltip from './SpiffTooltip';

type OwnProps = {
  'data-qa'?: string;
  description?: string;
  buttonLabel?: string;
  onConfirmation: (..._args: any[]) => any;
  title?: string;
  confirmButtonLabel?: string;
  kind?: 'text' | 'outlined' | 'contained';
  renderIcon?: any;
  iconDescription?: string | null;
  hasIconOnly?: boolean;
  classNameForModal?: string;
};

export default function ButtonWithConfirmation({
  description,
  buttonLabel,
  onConfirmation,
  'data-qa': dataQa,
  title,
  confirmButtonLabel,
  kind = 'contained',
  renderIcon,
  iconDescription = null,
  hasIconOnly = false,
  classNameForModal,
}: OwnProps) {
  const { t } = useTranslation();
  const [showConfirmationPrompt, setShowConfirmationPrompt] = useState(false);

  const handleShowConfirmationPrompt = () => {
    setShowConfirmationPrompt(true);
  };
  const handleConfirmationPromptCancel = () => {
    setShowConfirmationPrompt(false);
  };

  const handleConfirmation = () => {
    onConfirmation();
    setShowConfirmationPrompt(false);
  };

  const confirmationDialog = () => {
    return (
      <Dialog
        open={showConfirmationPrompt}
        onClose={handleConfirmationPromptCancel}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
        className={classNameForModal}
      >
        <DialogTitle id="alert-dialog-title">
          {title || t('are_you_sure')}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            {description ? description : null}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleConfirmationPromptCancel} color="primary">
            {t('cancel')}
          </Button>
          <Button onClick={handleConfirmation} color="primary" autoFocus>
            {confirmButtonLabel || t('ok')}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  if (hasIconOnly) {
    return (
      <>
        <SpiffTooltip title={iconDescription || ''} placement="top">
          <IconButton
            data-qa={dataQa}
            onClick={handleShowConfirmationPrompt}
            aria-label={iconDescription || ''}
          >
            {renderIcon}
          </IconButton>
        </SpiffTooltip>
        {confirmationDialog()}
      </>
    );
  }
  return (
    <>
      <Button
        data-qa={dataQa}
        onClick={handleShowConfirmationPrompt}
        variant={kind}
        color="error"
        startIcon={renderIcon}
        aria-label={iconDescription || ''}
      >
        {buttonLabel}
      </Button>
      {confirmationDialog()}
    </>
  );
}

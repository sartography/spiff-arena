import React, { useState } from 'react';
import CloseIcon from '@mui/icons-material/Close';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import WarningIcon from '@mui/icons-material/Warning';
import Button from '@mui/material/Button';
import IconButton from '@mui/material/IconButton';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { SnackbarCloseReason } from '@mui/material';
import { ObjectWithStringKeysAndValues } from '../interfaces';

type OwnProps = {
  title: string;
  children?: React.ReactNode;
  onClose?: (
    event: Event | React.SyntheticEvent<any, Event>,
    reason: SnackbarCloseReason,
  ) => void;
  type?: 'success' | 'error' | 'warning';
  hideCloseButton?: boolean;
  allowTogglingFullMessage?: boolean;
  timeout?: number;
  withBottomMargin?: boolean;
  'data-qa'?: string;
};

export function Notification({
  title,
  children,
  onClose,
  type = 'success',
  hideCloseButton = false,
  allowTogglingFullMessage = false,
  timeout,
  withBottomMargin = true,
  'data-qa': dataQa,
}: OwnProps) {
  const [showMessage, setShowMessage] = useState<boolean>(
    !allowTogglingFullMessage,
  );

  let iconComponent = <CheckCircleIcon />;
  if (type === 'error') {
    iconComponent = <ErrorIcon />;
  } else if (type === 'warning') {
    iconComponent = <WarningIcon />;
  }

  const additionalProps: ObjectWithStringKeysAndValues = {};
  if (dataQa) {
    additionalProps['data-qa'] = dataQa;
  }

  return (
    <Snackbar
      open
      anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      autoHideDuration={timeout}
      onClose={onClose}
      // eslint-disable-next-line react/jsx-props-no-spreading
      {...additionalProps}
    >
      <Alert
        icon={iconComponent}
        severity={type}
        action={
          <>
            {allowTogglingFullMessage && (
              <Button
                color="inherit"
                size="small"
                onClick={() => setShowMessage(!showMessage)}
              >
                {showMessage ? 'Hide' : 'Details'}
              </Button>
            )}
            {!hideCloseButton && (
              <IconButton
                size="small"
                aria-label="close"
                color="inherit"
                onClick={(event) => {
                  if (onClose) {
                    onClose(event, 'escapeKeyDown');
                  }
                }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            )}
          </>
        }
        sx={{ mb: withBottomMargin ? 2 : 0 }}
      >
        <strong>{title}</strong>
        {showMessage && <div>{children}</div>}
      </Alert>
    </Snackbar>
  );
}

import React from 'react';
import { useTranslation } from 'react-i18next';
import { type FallbackProps, useErrorBoundary } from 'react-error-boundary';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';

export function ErrorBoundaryFallback({ error }: FallbackProps) {
  // This is displayed if the ErrorBoundary catches an error when rendering the form.
  const { resetBoundary } = useErrorBoundary();
  const { t } = useTranslation();
  const errorMessage = error instanceof Error ? error.message : String(error);

  // print the error to the console so we can debug issues
  console.error(error);

  return (
    <Alert
      severity="error"
      action={
        <Button color="inherit" size="small" onClick={resetBoundary}>
          {t('try_again')}
        </Button>
      }
    >
      <AlertTitle>{t('something_went_wrong')}</AlertTitle>
      <p>{t('unexpected_error_call_admin')}</p>
      <p>{errorMessage}</p>
    </Alert>
  );
}

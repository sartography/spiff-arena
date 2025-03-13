import React from 'react';
import { useErrorBoundary } from 'react-error-boundary';
import Button from '@mui/material/Button';
import Alert from '@mui/material/Alert';
import AlertTitle from '@mui/material/AlertTitle';

type ErrorProps = {
  error: Error;
};

export function ErrorBoundaryFallback({ error }: ErrorProps) {
  // This is displayed if the ErrorBoundary catches an error when rendering the form.
  const { resetBoundary } = useErrorBoundary();

  // print the error to the console so we can debug issues
  console.error(error);

  return (
    <Alert
      severity="error"
      action={
        <Button color="inherit" size="small" onClick={resetBoundary}>
          Try again
        </Button>
      }
    >
      <AlertTitle>Something Went Wrong.</AlertTitle>
      <p>
        We encountered an unexpected error. Please try again. If the problem
        persists, please contact your administrator.
      </p>
      <p>{error.message}</p>
    </Alert>
  );
}

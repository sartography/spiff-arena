import { Button } from '@carbon/react';
import React from 'react';
import { useErrorBoundary } from 'react-error-boundary';

import { Notification } from './components/Notification';

type ErrorProps = {
  error: Error;
};

export function ErrorBoundaryFallback({ error }: ErrorProps) {
  // This is displayed if the ErrorBoundary catches an error when rendering the form.
  const { resetBoundary } = useErrorBoundary();

  // print the error to the console so we can debug issues
  console.error(error);

  return (
    <Notification
      title="Something Went Wrong."
      onClose={() => resetBoundary()}
      type="error"
    >
      <p>
        We encountered an unexpected error. Please try again. If the problem
        persists, please contact your administrator.
      </p>
      <p>{error.message}</p>
      <Button onClick={resetBoundary}>Try again</Button>
    </Notification>
  );
}

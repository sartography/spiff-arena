import { useContext } from 'react';
import ErrorContext from 'src/contexts/ErrorContext';
import { Notification } from './Notification';

export default function ErrorDisplay() {
  const [errorObject, setErrorObject] = (useContext as any)(ErrorContext);

  let errorTag = null;
  if (errorObject) {
    let sentryLinkTag = null;
    if (errorObject.sentry_link) {
      sentryLinkTag = (
        <span>
          {
            ': Find details about this error here (it may take a moment to become available): '
          }
          <a href={errorObject.sentry_link} target="_blank" rel="noreferrer">
            {errorObject.sentry_link}
          </a>
        </span>
      );
    }

    let message = <div>{errorObject.message}</div>;
    let title = 'Error:';
    if ('task_name' in errorObject && errorObject.task_name) {
      title = 'Error in python script:';
      message = (
        <>
          <br />
          <div>
            Task: {errorObject.task_name} ({errorObject.task_id})
          </div>
          <div>File name: {errorObject.file_name}</div>
          <div>Line number in script task: {errorObject.line_number}</div>
          <br />
          <div>{errorObject.message}</div>
        </>
      );
    }

    errorTag = (
      <Notification
        title={title}
        onClose={() => setErrorObject(null)}
        type="error"
      >
        {message}
        {sentryLinkTag}
      </Notification>
    );
  }

  return errorTag;
}

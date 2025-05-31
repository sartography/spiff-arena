import React, { SyntheticEvent } from 'react';
import { Alert, AlertTitle } from '@mui/material';
import { useTranslation } from 'react-i18next';
import useAPIError from '../hooks/UseApiError';
import {
  ErrorForDisplay,
  ProcessInstanceEventErrorDetail,
  ProcessInstanceLogEntry,
  TestCaseErrorDetails,
} from '../interfaces';

const defaultMessageClassName = 'failure-string';

function errorDetailDisplay(
  errorObject: any,
  propertyName: string,
  title: string,
) {
  // Creates a bit of html for displaying a single error property if it exists.
  let value = errorObject[propertyName];
  if (propertyName in errorObject && value) {
    if (typeof value === 'object') {
      value = JSON.stringify(value);
    }
    return (
      <div className="error_info">
        <span className="error_title">{title}:</span>
        {value}
      </div>
    );
  }
  return null;
}

export const errorForDisplayFromString = (errorMessage: string) => {
  const errorForDisplay: ErrorForDisplay = {
    message: errorMessage,
    messageClassName: defaultMessageClassName,
  };
  return errorForDisplay;
};

export const errorForDisplayFromProcessInstanceErrorDetail = (
  processInstanceEvent: ProcessInstanceLogEntry,
  processInstanceErrorEventDetail: ProcessInstanceEventErrorDetail,
) => {
  const errorForDisplay: ErrorForDisplay = {
    message: processInstanceErrorEventDetail.message,
    messageClassName: defaultMessageClassName,
    task_name: processInstanceEvent.task_definition_name,
    task_id: processInstanceEvent.task_definition_identifier,
    line_number: processInstanceErrorEventDetail.task_line_number,
    error_line: processInstanceErrorEventDetail.task_line_contents,
    task_trace: processInstanceErrorEventDetail.task_trace,
    stacktrace: processInstanceErrorEventDetail.stacktrace,
  };
  return errorForDisplay;
};

export const errorForDisplayFromTestCaseErrorDetails = (
  testCaseErrorDetails: TestCaseErrorDetails,
) => {
  const errorForDisplay: ErrorForDisplay = {
    message: testCaseErrorDetails.error_messages.join('\n'),
    messageClassName: defaultMessageClassName,
    task_name: testCaseErrorDetails.task_bpmn_name,
    task_id: testCaseErrorDetails.task_bpmn_identifier,
    line_number: testCaseErrorDetails.task_line_number,
    error_line: testCaseErrorDetails.task_line_contents,
    task_trace: testCaseErrorDetails.task_trace,
    stacktrace: testCaseErrorDetails.stacktrace,

    task_type: testCaseErrorDetails.task_bpmn_type,
    output_data: testCaseErrorDetails.output_data,
    expected_data: testCaseErrorDetails.expected_data,
  };
  return errorForDisplay;
};

export const childrenForErrorObject = (errorObject: ErrorForDisplay) => {
  let sentryLinkTag = null;
  const { t } = useTranslation();
  if (errorObject.sentry_link) {
    sentryLinkTag = (
      <span>
        {t('error_details_link_prefix')}
        <a href={errorObject.sentry_link} target="_blank" rel="noreferrer">
          {errorObject.sentry_link}
        </a>
      </span>
    );
  }

  const message = (
    <div className={errorObject.messageClassName}>{errorObject.message}</div>
  );
  const taskName = errorDetailDisplay(errorObject, 'task_name', t('task_name'));
  const taskId = errorDetailDisplay(errorObject, 'task_id', t('task_id'));
  const fileName = errorDetailDisplay(errorObject, 'file_name', t('file_name'));
  const lineNumber = errorDetailDisplay(
    errorObject,
    'line_number',
    t('line_number'),
  );
  const errorLine = errorDetailDisplay(errorObject, 'error_line', t('context'));
  const taskType = errorDetailDisplay(errorObject, 'task_type', t('task_type'));
  const outputData = errorDetailDisplay(
    errorObject,
    'output_data',
    t('output_data'),
  );
  const expectedData = errorDetailDisplay(
    errorObject,
    'expected_data',
    t('expected_data'),
  );
  let codeTrace = null;
  if (errorObject.task_trace && errorObject.task_trace.length > 0) {
    codeTrace = (
      <div className="error_info">
        <span className="error_title">{t('call_activity_trace')}</span>
        {errorObject.task_trace.reverse().join(' -> ')}
      </div>
    );
  } else if (errorObject.stacktrace) {
    codeTrace = (
      <pre className="error_info">
        <span className="error_title">{t('stacktrace')}:</span>
        {errorObject.stacktrace.reverse().map((a) => (
          <>
            {a}
            <br />
          </>
        ))}
      </pre>
    );
  }

  return [
    message,
    <br />,
    sentryLinkTag,
    taskName,
    taskId,
    fileName,
    lineNumber,
    errorLine,
    codeTrace,
    taskType,
    outputData,
    expectedData,
  ];
};

export function errorDisplayStateless(
  errorObject: ErrorForDisplay,
  onClose?: (event: SyntheticEvent) => void,
) {
  const { t } = useTranslation();
  const title = t('error');
  const hideCloseButton = !onClose;

  return (
    <Alert
      severity="error"
      onClose={onClose}
      action={
        hideCloseButton ? null : (
          <button type="button" onClick={onClose}>
            {t('close')}
          </button>
        )
      }
    >
      <AlertTitle>{title}</AlertTitle>
      {childrenForErrorObject(errorObject)}
    </Alert>
  );
}

export default function ErrorDisplay() {
  const { error: errorObject, removeError } = useAPIError();
  const handleRemoveError = (_event: SyntheticEvent) => {
    removeError();
  };
  let errorTag = null;

  if (errorObject) {
    errorTag = errorDisplayStateless(errorObject, handleRemoveError);
  }
  return errorTag;
}

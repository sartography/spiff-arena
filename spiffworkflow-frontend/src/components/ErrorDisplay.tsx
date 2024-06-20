import { Notification } from './Notification';
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

  const message = (
    <div className={errorObject.messageClassName}>{errorObject.message}</div>
  );
  const taskName = errorDetailDisplay(errorObject, 'task_name', 'Task Name');
  const taskId = errorDetailDisplay(errorObject, 'task_id', 'Task ID');
  const fileName = errorDetailDisplay(errorObject, 'file_name', 'File Name');
  const lineNumber = errorDetailDisplay(
    errorObject,
    'line_number',
    'Line Number',
  );
  const errorLine = errorDetailDisplay(errorObject, 'error_line', 'Context');
  const taskType = errorDetailDisplay(errorObject, 'task_type', 'Task Type');
  const outputData = errorDetailDisplay(
    errorObject,
    'output_data',
    'Output Data',
  );
  const expectedData = errorDetailDisplay(
    errorObject,
    'expected_data',
    'Expected Data',
  );
  let codeTrace = null;
  if (errorObject.task_trace && errorObject.task_trace.length > 0) {
    codeTrace = (
      <div className="error_info">
        <span className="error_title">Call Activity Trace:</span>
        {errorObject.task_trace.reverse().join(' -> ')}
      </div>
    );
  } else if (errorObject.stacktrace) {
    codeTrace = (
      <pre className="error_info">
        <span className="error_title">Stacktrace:</span>
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

export function ErrorDisplayStateless(
  errorObject: ErrorForDisplay,
  onClose?: Function,
) {
  const title = 'Error:';
  const hideCloseButton = !onClose;

  return (
    <Notification
      title={title}
      onClose={onClose}
      hideCloseButton={hideCloseButton}
      type="error"
    >
      <>{childrenForErrorObject(errorObject)}</>
    </Notification>
  );
}

export default function ErrorDisplay() {
  const errorObject = useAPIError().error;
  const { removeError } = useAPIError();
  let errorTag = null;

  if (errorObject) {
    errorTag = ErrorDisplayStateless(errorObject, removeError);
  }
  return errorTag;
}

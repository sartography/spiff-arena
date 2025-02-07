import { Rule, CheckCircle, Cancel } from '@mui/icons-material';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
} from '@mui/material';
import { useState } from 'react';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import HttpService from '../services/HttpService';
import { ProcessFile, TestCaseResult, TestCaseResults } from '../interfaces';
import {
  childrenForErrorObject,
  errorForDisplayFromTestCaseErrorDetails,
} from './ErrorDisplay';
import SpiffTooltip from './SpiffTooltip';

type OwnProps = {
  processModelFile?: ProcessFile;
  titleText: string;
  classNameForModal?: string;
};

export default function ProcessModelTestRun({
  processModelFile,
  titleText,
  classNameForModal,
}: OwnProps) {
  const [testCaseResults, setTestCaseResults] =
    useState<TestCaseResults | null>(null);
  const [showTestCaseResultsModal, setShowTestCaseResultsModal] =
    useState<boolean>(false);
  const { targetUris } = useUriListForPermissions();

  const onProcessModelTestRunSuccess = (result: TestCaseResults) => {
    setTestCaseResults(result);
  };

  const processModelTestRunResultTag = () => {
    if (testCaseResults) {
      if (testCaseResults.all_passed) {
        return (
          <SpiffTooltip title="All BPMN unit tests passed" placement="top">
            <IconButton
              color="success"
              aria-label="All BPMN unit tests passed"
              onClick={() => setShowTestCaseResultsModal(true)}
            >
              <CheckCircle />
            </IconButton>
          </SpiffTooltip>
        );
      }
      return (
        <SpiffTooltip title="BPMN unit tests failed" placement="top">
          <IconButton
            color="error"
            aria-label="BPMN unit tests failed"
            onClick={() => setShowTestCaseResultsModal(true)}
          >
            <Cancel />
          </IconButton>
        </SpiffTooltip>
      );
    }
    return null;
  };

  const onProcessModelTestRun = () => {
    const httpMethod = 'POST';
    setTestCaseResults(null);

    let queryParams = '';
    if (processModelFile) {
      queryParams = `?test_case_file=${processModelFile.name}`;
    }

    HttpService.makeCallToBackend({
      path: `${targetUris.processModelTestsPath}${queryParams}`,
      successCallback: onProcessModelTestRunSuccess,
      httpMethod,
    });
  };

  const testCaseFormattedResultTag = () => {
    if (!testCaseResults) {
      return null;
    }

    const passingRows: any[] = [];
    const failingRows: any[] = [];

    testCaseResults.passing.forEach((testCaseResult: TestCaseResult) => {
      passingRows.push(<p>{testCaseResult.test_case_identifier}</p>);
    });

    testCaseResults.failing
      .slice(0, 2)
      .forEach((testCaseResult: TestCaseResult) => {
        if (testCaseResult.test_case_error_details) {
          const errorForDisplay = errorForDisplayFromTestCaseErrorDetails(
            testCaseResult.test_case_error_details,
          );
          const errorChildren = childrenForErrorObject(errorForDisplay);
          failingRows.push(
            <>
              <br />
              <p>
                Test Case:{' '}
                <strong>{testCaseResult.test_case_identifier}</strong>
              </p>
              {errorChildren}
            </>,
          );
        }
      });

    return (
      <>
        <p>Passing: {testCaseResults.passing.length}</p>
        <p>Failing: {testCaseResults.failing.length}</p>
        <br />
        {failingRows.length > 0 ? (
          <>
            <p>Failure Details:</p>
            {failingRows}
          </>
        ) : null}
        {passingRows.length > 0 ? (
          <>
            <p>Successful Test Cases:</p>
            {passingRows}
          </>
        ) : null}
      </>
    );
  };

  const testCaseResultsModal = () => {
    if (!testCaseResults) {
      return null;
    }

    let modalHeading = 'All Tests PASSED';
    if (!testCaseResults.all_passed) {
      modalHeading = 'Some Tests FAILED';
    }
    return (
      <Dialog
        open={showTestCaseResultsModal}
        onClose={() => setShowTestCaseResultsModal(false)}
        className={classNameForModal}
      >
        <DialogTitle>{modalHeading}</DialogTitle>
        <DialogContent>{testCaseFormattedResultTag()}</DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTestCaseResultsModal(false)}>OK</Button>
        </DialogActions>
      </Dialog>
    );
  };

  const buttonElement = () => {
    return (
      <SpiffTooltip title={titleText} placement="top">
        <IconButton
          color="primary"
          aria-label={titleText}
          onClick={() => onProcessModelTestRun()}
        >
          <Rule />
        </IconButton>
      </SpiffTooltip>
    );
  };

  return (
    <>
      {testCaseResultsModal()}
      {buttonElement()}
      {processModelTestRunResultTag()}
    </>
  );
}

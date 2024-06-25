import { Rule, Checkmark, Close } from '@carbon/icons-react';
import { Button, Modal } from '@carbon/react';
import { useState } from 'react';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import HttpService from '../services/HttpService';
import { ProcessFile, TestCaseResult, TestCaseResults } from '../interfaces';
import {
  childrenForErrorObject,
  errorForDisplayFromTestCaseErrorDetails,
} from './ErrorDisplay';

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
          <Button
            kind="ghost"
            className="green-icon"
            renderIcon={Checkmark}
            iconDescription="All BPMN unit tests passed"
            hasIconOnly
            size="lg"
            onClick={() => setShowTestCaseResultsModal(true)}
          />
        );
      }
      return (
        <Button
          kind="ghost"
          className="red-icon"
          renderIcon={Close}
          iconDescription="BPMN unit tests failed"
          hasIconOnly
          size="lg"
          onClick={() => setShowTestCaseResultsModal(true)}
        />
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
      <Modal
        open={showTestCaseResultsModal}
        data-qa="test-case-results-modal"
        modalHeading={modalHeading}
        modalLabel="Test Case Results"
        primaryButtonText="OK"
        onRequestSubmit={() => setShowTestCaseResultsModal(false)}
        onRequestClose={() => setShowTestCaseResultsModal(false)}
        className={classNameForModal}
      >
        {testCaseFormattedResultTag()}
      </Modal>
    );
  };

  const buttonElement = () => {
    return (
      <Button
        kind="ghost"
        renderIcon={Rule}
        iconDescription={titleText}
        hasIconOnly
        size="lg"
        onClick={() => onProcessModelTestRun()}
      />
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

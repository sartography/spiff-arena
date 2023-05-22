import { PlayOutline, Checkmark, Close } from '@carbon/icons-react';
import { Button, Modal } from '@carbon/react';
import { useState } from 'react';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import HttpService from '../services/HttpService';
import { ProcessFile } from '../interfaces';

type OwnProps = {
  processModelFile: ProcessFile;
};

export default function ProcessModelTestRun({ processModelFile }: OwnProps) {
  const [testCaseResults, setTestCaseResults] = useState<any>(null);
  const [showTestCaseResultsModal, setShowTestCaseResultsModal] =
    useState<boolean>(false);
  const { targetUris } = useUriListForPermissions();

  const onProcessModelTestRunSuccess = (result: any) => {
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
            iconDescription="PASS"
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
          iconDescription="FAILS"
          hasIconOnly
          size="lg"
          onClick={() => setShowTestCaseResultsModal(true)}
        />
      );
    }
    return null;
  };

  const onProcessModelTestRun = (fileName: string) => {
    const httpMethod = 'POST';
    setTestCaseResults(null);

    HttpService.makeCallToBackend({
      path: `${targetUris.processModelTestsPath}?test_case_file=${fileName}`,
      successCallback: onProcessModelTestRunSuccess,
      httpMethod,
    });
  };

  const testCaseResultsModal = () => {
    return (
      <Modal
        open={showTestCaseResultsModal}
        data-qa="test-case-results-modal"
        modalHeading="RESULT FOR"
        modalLabel="LABLE"
        primaryButtonText="OK"
        onRequestSubmit={() => setShowTestCaseResultsModal(false)}
        onRequestClose={() => setShowTestCaseResultsModal(false)}
      >
        {JSON.stringify(testCaseResults)}
      </Modal>
    );
  };

  return (
    <>
      {testCaseResultsModal()}
      <Button
        kind="ghost"
        renderIcon={PlayOutline}
        iconDescription="Run Test"
        hasIconOnly
        size="lg"
        onClick={() => onProcessModelTestRun(processModelFile.name)}
      />
      {processModelTestRunResultTag()}
    </>
  );
}

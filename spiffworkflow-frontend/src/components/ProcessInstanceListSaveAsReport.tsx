import { useState } from 'react';
import {
  Button,
  TextInput,
  Stack,
  Modal,
  // @ts-ignore
} from '@carbon/react';
import { ProcessInstanceReport, ReportMetadata } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onSuccess: (..._args: any[]) => any;
  buttonText?: string;
  buttonClassName?: string;
  processInstanceReportSelection?: ProcessInstanceReport | null;
  reportMetadata: ReportMetadata | null;
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  processInstanceReportSelection,
  buttonClassName,
  buttonText = 'Save as Perspective',
  reportMetadata,
}: OwnProps) {
  const [identifier, setIdentifier] = useState<string>(
    processInstanceReportSelection?.identifier || '',
  );
  const [showSaveForm, setShowSaveForm] = useState<boolean>(false);

  const isEditMode = () => {
    return (
      processInstanceReportSelection &&
      processInstanceReportSelection.identifier === identifier
    );
  };

  const responseHandler = (result: any) => {
    if (result) {
      onSuccess(result, isEditMode() ? 'edit' : 'new');
    }
  };

  const handleSaveFormClose = () => {
    setIdentifier(processInstanceReportSelection?.identifier || '');
    setShowSaveForm(false);
  };

  const addProcessInstanceReport = (event: any) => {
    event.preventDefault();

    let path = `/process-instances/reports`;
    let httpMethod = 'POST';
    if (isEditMode() && processInstanceReportSelection) {
      httpMethod = 'PUT';
      path = `${path}/${processInstanceReportSelection.id}`;
    }

    HttpService.makeCallToBackend({
      path,
      successCallback: responseHandler,
      httpMethod,
      postBody: {
        identifier,
        report_metadata: reportMetadata,
      },
    });
    handleSaveFormClose();
  };

  let textInputComponent = null;
  textInputComponent = (
    <TextInput
      id="identifier"
      name="identifier"
      labelText="Identifier"
      className="no-wrap"
      inline
      value={identifier}
      onChange={(e: any) => setIdentifier(e.target.value)}
    />
  );

  let descriptionText =
    'Save the current columns and filters as a perspective so you can come back to this view in the future.';
  if (processInstanceReportSelection) {
    descriptionText =
      'Keep the identifier the same and click Save to update the current perspective. Change the identifier if you want to save the current view with a new name.';
  }

  return (
    <Stack gap={5} orientation="horizontal">
      <Modal
        open={showSaveForm}
        modalHeading="Save Perspective"
        primaryButtonText="Save"
        primaryButtonDisabled={!identifier}
        onRequestSubmit={addProcessInstanceReport}
        onRequestClose={handleSaveFormClose}
        hasScrollingContent
        aria-label="save perspective"
      >
        <p className="data-table-description">{descriptionText}</p>
        {textInputComponent}
      </Modal>
      <Button
        kind="tertiary"
        className={buttonClassName}
        onClick={() => {
          setIdentifier(processInstanceReportSelection?.identifier || '');
          setShowSaveForm(true);
        }}
      >
        {buttonText}
      </Button>
    </Stack>
  );
}

import { useState } from 'react';
import {
  Button,
  TextInput,
  Stack,
  Modal,
  // @ts-ignore
} from '@carbon/react';
import {
  ReportFilter,
  ProcessInstanceReport,
  ProcessModel,
  ReportColumn,
  ReportMetadata,
  User,
} from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onSuccess: (..._args: any[]) => any;
  columnArray: ReportColumn[];
  orderBy: string;
  processModelSelection: ProcessModel | null;
  processInitiatorSelection: User | null;
  processStatusSelection: string[];
  startFromSeconds: string | null;
  startToSeconds: string | null;
  endFromSeconds: string | null;
  endToSeconds: string | null;
  buttonText?: string;
  buttonClassName?: string;
  processInstanceReportSelection?: ProcessInstanceReport | null;
  reportMetadata: ReportMetadata;
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  columnArray,
  orderBy,
  processModelSelection,
  processInitiatorSelection,
  processInstanceReportSelection,
  processStatusSelection,
  startFromSeconds,
  startToSeconds,
  endFromSeconds,
  endToSeconds,
  buttonClassName,
  buttonText = 'Save as Perspective',
  reportMetadata,
}: OwnProps) {
  const [identifier, setIdentifier] = useState<string>(
    processInstanceReportSelection?.identifier || ''
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

    // // TODO: make a field to set this
    // let orderByArray = ['-start_in_seconds', '-id'];
    // if (orderBy) {
    //   orderByArray = orderBy.split(',').filter((n) => n);
    // }
    // const filterByArray: any = [];
    //
    // if (processModelSelection) {
    //   filterByArray.push({
    //     field_name: 'process_model_identifier',
    //     field_value: processModelSelection.id,
    //   });
    // }
    //
    // if (processInitiatorSelection) {
    //   filterByArray.push({
    //     field_name: 'process_initiator_username',
    //     field_value: processInitiatorSelection.username,
    //   });
    // }
    //
    // if (processStatusSelection.length > 0) {
    //   filterByArray.push({
    //     field_name: 'process_status',
    //     field_value: processStatusSelection.join(','),
    //     operator: 'in',
    //   });
    // }
    //
    // if (startFromSeconds) {
    //   filterByArray.push({
    //     field_name: 'start_from',
    //     field_value: startFromSeconds,
    //   });
    // }
    //
    // if (startToSeconds) {
    //   filterByArray.push({
    //     field_name: 'start_to',
    //     field_value: startToSeconds,
    //   });
    // }
    //
    // if (endFromSeconds) {
    //   filterByArray.push({
    //     field_name: 'end_from',
    //     field_value: endFromSeconds,
    //   });
    // }
    //
    // if (endToSeconds) {
    //   filterByArray.push({
    //     field_name: 'end_to',
    //     field_value: endToSeconds,
    //   });
    // }
    //
    // reportMetadata.filter_by.forEach((reportFilter: ReportFilter) => {
    //   columnArray.forEach((reportColumn: ReportColumn) => {
    //     if (
    //       reportColumn.accessor === reportFilter.field_name &&
    //       reportColumn.filterable
    //     ) {
    //       filterByArray.push(reportFilter);
    //     }
    //   });
    // });

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
      >
        <p className="data-table-description">{descriptionText}</p>
        {textInputComponent}
      </Modal>
      <Button
        kind=""
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

import { useState } from 'react';
import {
  Button,
  TextInput,
  Form,
  Stack,
  // @ts-ignore
} from '@carbon/react';
import { ProcessInstanceReport, ProcessModel } from '../interfaces';
import HttpService from '../services/HttpService';

type OwnProps = {
  onSuccess: (..._args: any[]) => any;
  columnArray: { Header: string; accessor: string };
  orderBy: string;
  processModelSelection: ProcessModel | null;
  processStatusSelection: string[];
  startFromSeconds: string | null;
  startToSeconds: string | null;
  endFromSeconds: string | null;
  endToSeconds: string | null;
  buttonText?: string;
  buttonClassName?: string;
  processInstanceReportSelection?: ProcessInstanceReport | null;
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  columnArray,
  orderBy,
  processModelSelection,
  processInstanceReportSelection,
  processStatusSelection,
  startFromSeconds,
  startToSeconds,
  endFromSeconds,
  endToSeconds,
  buttonText = 'Save as Perspective',
  buttonClassName,
}: OwnProps) {
  const [identifier, setIdentifier] = useState<string>(
    processInstanceReportSelection?.identifier || ''
  );

  const hasIdentifier = () => {
    return identifier?.length > 0;
  };

  const responseHandler = (result: any) => {
    if (result) {
      onSuccess(result);
    }
  };

  const isEditMode = () => {
    return !!processInstanceReportSelection;
  };

  const addProcessInstanceReport = (event: any) => {
    event.preventDefault();

    const orderByArray = orderBy.split(',').filter((n) => n);
    const filterByArray: any = [];

    if (processModelSelection) {
      filterByArray.push({
        field_name: 'process_model_identifier',
        field_value: processModelSelection.id,
      });
    }

    if (processStatusSelection.length > 0) {
      filterByArray.push({
        field_name: 'process_status',
        field_value: processStatusSelection[0], // TODO: support more than one status
      });
    }

    if (startFromSeconds) {
      filterByArray.push({
        field_name: 'start_from',
        field_value: startFromSeconds,
      });
    }

    if (startToSeconds) {
      filterByArray.push({
        field_name: 'start_to',
        field_value: startToSeconds,
      });
    }

    if (endFromSeconds) {
      filterByArray.push({
        field_name: 'end_from',
        field_value: endFromSeconds,
      });
    }

    if (endToSeconds) {
      filterByArray.push({
        field_name: 'end_to',
        field_value: endToSeconds,
      });
    }

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
        report_metadata: {
          columns: columnArray,
          order_by: orderByArray,
          filter_by: filterByArray,
        },
      },
    });
  };

  let textInputComponent = null;
  if (!isEditMode()) {
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
  }

  return (
    <Form onSubmit={addProcessInstanceReport}>
      <Stack gap={5} orientation="horizontal">
        {textInputComponent}
        <Button
          disabled={!hasIdentifier()}
          size="sm"
          type="submit"
          className={buttonClassName}
        >
          {buttonText}
        </Button>
      </Stack>
    </Form>
  );
}

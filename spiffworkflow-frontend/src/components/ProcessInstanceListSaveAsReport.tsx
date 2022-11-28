import { useState } from 'react';
// TODO: carbon controls
/*
import {
  Button,
  Textbox,
  // @ts-ignore
} from '@carbon/react';
*/
import { ProcessModel } from '../interfaces';
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
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  columnArray,
  orderBy,
  processModelSelection,
  processStatusSelection,
  startFromSeconds,
  startToSeconds,
  endFromSeconds,
  endToSeconds,
  buttonText = 'Save as Perspective',
}: OwnProps) {
  const [identifier, setIdentifier] = useState('');

  const hasIdentifier = () => {
    return identifier?.length > 0;
  };

  const responseHandler = (result: any) => {
    if (result.ok === true) {
      onSuccess(identifier);
    }
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

    HttpService.makeCallToBackend({
      path: `/process-instances/reports`,
      successCallback: responseHandler,
      httpMethod: 'POST',
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

  return (
    <form onSubmit={addProcessInstanceReport}>
      <label htmlFor="identifier">
        identifier:
        <input
          name="identifier"
          id="identifier"
          type="text"
          value={identifier}
          onChange={(e) => setIdentifier(e.target.value)}
        />
      </label>
      <button disabled={!hasIdentifier()} type="submit">
        {buttonText}
      </button>
    </form>
  );
}

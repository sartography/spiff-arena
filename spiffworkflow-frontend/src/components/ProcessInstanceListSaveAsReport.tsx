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
  buttonText?: string;
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  columnArray,
  orderBy,
  processModelSelection,
  buttonText = 'Save as Perspective',
}: OwnProps) {
  const [identifier, setIdentifier] = useState('');

  const hasIdentifier = () => {
    return identifier?.length > 0;
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

    HttpService.makeCallToBackend({
      path: `/process-instances/reports`,
      successCallback: onSuccess,
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

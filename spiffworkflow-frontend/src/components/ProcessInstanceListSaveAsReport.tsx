import { useState } from 'react';
// TODO: carbon controls
/*
import {
  Button,
  Textbox,
  // @ts-ignore
} from '@carbon/react';
*/
import HttpService from '../services/HttpService';

type OwnProps = {
  onSuccess: (..._args: any[]) => any;
  columns: string;
  orderBy: string;
  filterBy: string;
  buttonText?: string;
};

export default function ProcessInstanceListSaveAsReport({
  onSuccess,
  columns,
  orderBy,
  filterBy,
  buttonText = 'Save as New Perspective',
}: OwnProps) {
  const [identifier, setIdentifier] = useState('');

  const hasIdentifier = () => {
    return identifier?.length > 0;
  };

  const addProcessInstanceReport = (event: any) => {
    event.preventDefault();

    const columnArray = columns.split(',').map((column) => {
      return { Header: column, accessor: column };
    });
    const orderByArray = orderBy.split(',').filter((n) => n);

    const filterByArray = filterBy
      .split(',')
      .map((filterByItem) => {
        const [fieldName, fieldValue] = filterByItem.split('=');
        if (fieldValue) {
          return {
            field_name: fieldName,
            operator: 'equals',
            field_value: fieldValue,
          };
        }
        return null;
      })
      .filter((n) => n);

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
      <button disabled={!hasIdentifier()} type="submit">{buttonText}</button>
    </form>
  );
}

import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';

export default function ProcessInstanceReportNew() {
  const navigate = useNavigate();

  const [identifier, setIdentifier] = useState('');
  const [columns, setColumns] = useState('');
  const [orderBy, setOrderBy] = useState('');
  const [filterBy, setFilterBy] = useState('');

  const navigateToNewProcessInstance = (_result: any) => {
    navigate(`/process-instances/reports/${identifier}`);
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
      successCallback: navigateToNewProcessInstance,
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
    <>
      <ProcessBreadcrumb />
      <h1>Add Process Instance Perspective</h1>
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
        <br />
        <label htmlFor="columns">
          columns:
          <input
            name="columns"
            id="columns"
            type="text"
            value={columns}
            onChange={(e) => setColumns(e.target.value)}
          />
        </label>
        <br />
        <label htmlFor="order_by">
          order_by:
          <input
            name="order_by"
            id="order_by"
            type="text"
            value={orderBy}
            onChange={(e) => setOrderBy(e.target.value)}
          />
        </label>
        <br />
        <br />
        <p>Like: month=3,milestone=2</p>
        <label htmlFor="filter_by">
          filter_by:
          <input
            name="filter_by"
            id="filter_by"
            type="text"
            value={filterBy}
            onChange={(e) => setFilterBy(e.target.value)}
          />
        </label>
        <br />
        <button type="submit">Submit</button>
      </form>
    </>
  );
}

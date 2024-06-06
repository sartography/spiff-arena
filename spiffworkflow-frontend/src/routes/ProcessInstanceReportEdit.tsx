import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import HttpService from '../services/HttpService';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';

type ReportColumn = {
  Header: string;
  accessor: string;
};

type ReportFilterBy = {
  field_name: string;
  operator: string;
  field_value: string;
};

export default function ProcessInstanceReportEdit() {
  const params = useParams();
  const navigate = useNavigate();

  const [columns, setColumns] = useState('');
  const [orderBy, setOrderBy] = useState('');
  const [filterBy, setFilterBy] = useState('');

  const navigateToProcessInstanceReport = (_result: any) => {
    navigate(`/process-instances/reports/${params.report_identifier}`);
  };

  const navigateToProcessInstanceReports = (_result: any) => {
    navigate(`/process-instances/reports`);
  };

  useEffect(() => {
    const processResult = (result: any) => {
      const reportMetadata = result.report_metadata;
      const columnCsv = reportMetadata.columns
        .map((column: ReportColumn) => column.accessor)
        .join(',');
      setColumns(columnCsv);

      if (reportMetadata.order_by) {
        setOrderBy(reportMetadata.order_by.join(','));
      }
      const filterByCsv = reportMetadata.filter_by
        .map(
          (filterByItem: ReportFilterBy) =>
            `${filterByItem.field_name}=${filterByItem.field_value}`,
        )
        .join(',');
      setFilterBy(filterByCsv);
    };
    function getProcessInstanceReport() {
      HttpService.makeCallToBackend({
        path: `/process-instances/reports/${params.report_identifier}?per_page=1`,
        successCallback: processResult,
      });
    }

    getProcessInstanceReport();
  }, [params.report_identifier]);

  const editProcessInstanceReport = (event: any) => {
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
      path: `/process-instances/reports/${params.report_identifier}`,
      successCallback: navigateToProcessInstanceReport,
      httpMethod: 'PUT',
      postBody: {
        report_metadata: {
          columns: columnArray,
          order_by: orderByArray,
          filter_by: filterByArray,
        },
      },
    });
  };

  const deleteProcessInstanceReport = () => {
    HttpService.makeCallToBackend({
      path: `/process-instances/reports/${params.report_identifier}`,
      successCallback: navigateToProcessInstanceReports,
      httpMethod: 'DELETE',
    });
  };

  return (
    <>
      <h1>Edit Process Instance Report: {params.report_identifier}</h1>
      <ButtonWithConfirmation
        description={`Delete Report ${params.report_identifier}?`}
        onConfirmation={deleteProcessInstanceReport}
        buttonLabel="Delete"
      />
      <br />
      <br />
      <form onSubmit={editProcessInstanceReport}>
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

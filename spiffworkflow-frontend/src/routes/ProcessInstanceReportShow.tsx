import { useEffect, useState } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';

// @ts-ignore
import { Button, Table } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';

import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import { getPageInfoFromSearchParams } from '../helpers';

const PER_PAGE_FOR_PROCESS_INSTANCE_REPORT = 500;

export default function ProcessInstanceReport() {
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processInstances, setProcessInstances] = useState([]);
  const [reportMetadata, setReportMetadata] = useState({});
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    const processResult = (result: any) => {
      const processInstancesFromApi = result.results;
      setProcessInstances(processInstancesFromApi);
      setReportMetadata(result.report_metadata);
      setPagination(result.pagination);
    };

    function getProcessInstances() {
      const { page, perPage } = getPageInfoFromSearchParams(
        searchParams,
        PER_PAGE_FOR_PROCESS_INSTANCE_REPORT
      );
      let query = `?page=${page}&per_page=${perPage}`;
      searchParams.forEach((value, key) => {
        if (key !== 'page' && key !== 'per_page') {
          query += `&${key}=${value}`;
        }
      });
      HttpService.makeCallToBackend({
        path: `/process-instances/reports/${params.report_identifier}${query}`,
        successCallback: processResult,
      });
    }

    getProcessInstances();
  }, [searchParams, params]);

  const buildTable = () => {
    const headers = (reportMetadata as any).columns.map((column: any) => {
      return <th>{(column as any).Header}</th>;
    });

    const rows = processInstances.map((row) => {
      const currentRow = (reportMetadata as any).columns.map((column: any) => {
        return <td>{(row as any)[column.accessor]}</td>;
      });
      return <tr key={(row as any).id}>{currentRow}</tr>;
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>{headers}</tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      PER_PAGE_FOR_PROCESS_INSTANCE_REPORT
    );
    return (
      <main>
        <ProcessBreadcrumb
          processModelId={params.process_model_id}
          processGroupId={params.process_group_id}
          linkProcessModel
        />
        <h1>Process Instance Report: {params.report_identifier}</h1>
        <Button
          href={`/admin/process-instances/reports/${params.report_identifier}/edit`}
        >
          Edit process instance report
        </Button>
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
        />
      </main>
    );
  }
  return null;
}

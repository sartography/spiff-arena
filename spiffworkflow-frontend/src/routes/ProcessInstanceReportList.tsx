import { useEffect, useState } from 'react';
// @ts-ignore
import { Button, Table } from '@carbon/react';
import { useParams, Link } from 'react-router-dom';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';

export default function ProcessInstanceReportList() {
  const params = useParams();
  const [processInstanceReports, setProcessInstanceReports] = useState([]);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/reports`,
      successCallback: setProcessInstanceReports,
    });
  }, [params]);

  const buildTable = () => {
    const rows = processInstanceReports.map((row) => {
      const rowToUse = row as any;
      return (
        <tr key={(row as any).id}>
          <td>
            <Link
              to={`/admin/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/reports/${rowToUse.identifier}`}
            >
              {rowToUse.identifier}
            </Link>
          </td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Identifier</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const headerStuff = (
    <>
      <ProcessBreadcrumb
        processGroupId={params.process_group_id}
        processModelId={params.process_model_id}
        linkProcessModel
      />
      <h2>Reports for Process Model: {params.process_model_id}</h2>
      <Button
        href={`/admin/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/reports/new`}
      >
        Add a process instance report
      </Button>
    </>
  );
  if (processInstanceReports?.length > 0) {
    return (
      <main>
        {headerStuff}
        {buildTable()}
      </main>
    );
  }
  return (
    <main>
      {headerStuff}
      <p>No reports found</p>
    </main>
  );
}

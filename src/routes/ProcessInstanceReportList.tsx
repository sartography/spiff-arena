import { useEffect, useState } from 'react';
// @ts-ignore
import { Button, Table } from '@carbon/react';
import { useParams, Link } from 'react-router-dom';
import HttpService from '../services/HttpService';

export default function ProcessInstanceReportList() {
  const params = useParams();
  const [processInstanceReports, setProcessInstanceReports] = useState([]);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/process-instances/reports`,
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
              to={`/admin/process-instances/reports/${rowToUse.identifier}`}
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
      <h1>Process Instance Reports</h1>
      <Button href="/admin/process-instances/reports/new">
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

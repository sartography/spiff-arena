import { useEffect, useState } from 'react';
// @ts-ignore
import { Button, Table } from '@carbon/react';
import { Link } from 'react-router-dom';
import { Can } from '@casl/react';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { PermissionsToCheck } from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';

export default function ProcessInstanceReportList() {
  const [processInstanceReports, setProcessInstanceReports] = useState([]);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processInstanceReportListPath]: ['POST'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/process-instances/reports`,
      successCallback: setProcessInstanceReports,
    });
  }, []);

  const buildTable = () => {
    const rows = processInstanceReports.map((row) => {
      const rowToUse = row as any;
      return (
        <tr key={(row as any).id}>
          <td>
            <Link to={`/process-instances?report_id=${rowToUse.id}`}>
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
      <h1>Process Instance Perspectives</h1>
      <Can I="POST" a={targetUris.processInstanceListPath} ability={ability}>
        <Button href="/process-instances/reports/new">
          Add a process instance perspective
        </Button>
      </Can>
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
      <p>No perspectives found</p>
    </main>
  );
}

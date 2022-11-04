import { useEffect, useState } from 'react';
import { Link, useSearchParams, useParams } from 'react-router-dom';
// @ts-ignore
import { Button, Table, Stack } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import { getPageInfoFromSearchParams } from '../helpers';
import { ProcessGroup } from '../interfaces';

export default function ProcessGroupShow() {
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const [processModels, setProcessModels] = useState([]);
  const [pagination, setPagination] = useState(null);

  useEffect(() => {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);

    const setProcessModelFromResult = (result: any) => {
      setProcessModels(result.results);
      setPagination(result.pagination);
    };
    const processResult = (result: any) => {
      setProcessGroup(result);
      HttpService.makeCallToBackend({
        path: `/process-models?process_group_identifier=${params.process_group_id}&per_page=${perPage}&page=${page}`,
        successCallback: setProcessModelFromResult,
      });
    };
    HttpService.makeCallToBackend({
      path: `/process-groups/${params.process_group_id}`,
      successCallback: processResult,
    });
  }, [params, searchParams]);

  const buildTable = () => {
    if (processGroup === null) {
      return null;
    }
    const rows = processModels.map((row) => {
      return (
        <tr key={(row as any).id}>
          <td>
            <Link
              to={`/admin/process-models/${processGroup.id}/${(row as any).id}`}
              data-qa="process-model-show-link"
            >
              {(row as any).id}
            </Link>
          </td>
          <td>{(row as any).display_name}</td>
        </tr>
      );
    });
    return (
      <div>
        <h3>Process Models</h3>
        <Table striped bordered>
          <thead>
            <tr>
              <th>Process Model Id</th>
              <th>Display Name</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </Table>
      </div>
    );
  };

  if (processGroup && pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            [`Process Group: ${processGroup.display_name}`],
          ]}
        />
        <ul>
          <Stack orientation="horizontal" gap={3}>
            <Button
              href={`/admin/process-models/${(processGroup as any).id}/new`}
            >
              Add a process model
            </Button>
            <Button
              href={`/admin/process-groups/${(processGroup as any).id}/edit`}
              variant="secondary"
            >
              Edit process group
            </Button>
          </Stack>
          <br />
          <br />
          <PaginationForTable
            page={page}
            perPage={perPage}
            pagination={pagination}
            tableToDisplay={buildTable()}
            path={`/admin/process-groups/${(processGroup as any).id}`}
          />
        </ul>
      </>
    );
  }
  return null;
}

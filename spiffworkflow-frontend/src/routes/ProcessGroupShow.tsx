import { useEffect, useState } from 'react';
import { Link, useSearchParams, useParams } from 'react-router-dom';
// @ts-ignore
import { Button, Table, Stack } from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import {
  getPageInfoFromSearchParams,
  modifyProcessModelPath,
  unModifyProcessModelPath,
} from '../helpers';
import { ProcessGroup, ProcessModel } from '../interfaces';

export default function ProcessGroupShow() {
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const [processModels, setProcessModels] = useState([]);
  const [processGroups, setProcessGroups] = useState([]);
  const [modelPagination, setModelPagination] = useState(null);
  const [groupPagination, setGroupPagination] = useState(null);

  useEffect(() => {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);

    const setProcessModelFromResult = (result: any) => {
      setProcessModels(result.results);
      setModelPagination(result.pagination);
    };
    const setProcessGroupFromResult = (result: any) => {
      setProcessGroups(result.results);
      setGroupPagination(result.pagination);
    };
    const processResult = (result: any) => {
      setProcessGroup(result);
      const unmodifiedProcessGroupId = unModifyProcessModelPath(
        (params as any).process_group_id
      );
      HttpService.makeCallToBackend({
        path: `/process-models?process_group_identifier=${unmodifiedProcessGroupId}&per_page=${perPage}&page=${page}`,
        successCallback: setProcessModelFromResult,
      });
      HttpService.makeCallToBackend({
        path: `/process-groups?process_group_identifier=${unmodifiedProcessGroupId}&per_page=${perPage}&page=${page}`,
        successCallback: setProcessGroupFromResult,
      });
    };
    HttpService.makeCallToBackend({
      path: `/process-groups/${params.process_group_id}`,
      successCallback: processResult,
    });
  }, [params, searchParams]);

  const buildModelTable = () => {
    if (processGroup === null) {
      return null;
    }
    const rows = processModels.map((row: ProcessModel) => {
      const modifiedProcessModelId: String = modifyProcessModelPath(
        (row as any).id
      );
      return (
        <tr key={row.id}>
          <td>
            <Link
              to={`/admin/process-models/${modifiedProcessModelId}`}
              data-qa="process-model-show-link"
            >
              {row.id}
            </Link>
          </td>
          <td>{row.display_name}</td>
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

  const buildGroupTable = () => {
    if (processGroup === null) {
      return null;
    }
    const rows = processGroups.map((row: ProcessGroup) => {
      const modifiedProcessGroupId: String = modifyProcessModelPath(row.id);
      return (
        <tr key={row.id}>
          <td>
            <Link
              to={`/admin/process-groups/${modifiedProcessGroupId}`}
              data-qa="process-model-show-link"
            >
              {row.id}
            </Link>
          </td>
          <td>{row.display_name}</td>
        </tr>
      );
    });
    return (
      <div>
        <h3>Process Groups</h3>
        <Table striped bordered>
          <thead>
            <tr>
              <th>Process Group Id</th>
              <th>Display Name</th>
            </tr>
          </thead>
          <tbody>{rows}</tbody>
        </Table>
      </div>
    );
  };

  if (processGroup && groupPagination && modelPagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    const modifiedProcessGroupId = modifyProcessModelPath(processGroup.id);
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            ['', `process_group:${processGroup.id}`],
          ]}
        />
        <ul>
          <Stack orientation="horizontal" gap={3}>
            <Button
              kind="secondary"
              href={`/admin/process-groups/new?parentGroupId=${processGroup.id}`}
            >
              Add a process group
            </Button>
            <Button
              href={`/admin/process-models/${modifiedProcessGroupId}/new`}
            >
              Add a process model
            </Button>
            <Button
              href={`/admin/process-groups/${modifiedProcessGroupId}/edit`}
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
            pagination={modelPagination}
            tableToDisplay={buildModelTable()}
            path={`/admin/process-groups/${processGroup.id}`}
          />
          <br />
          <br />
          <PaginationForTable
            page={page}
            perPage={perPage}
            pagination={groupPagination}
            tableToDisplay={buildGroupTable()}
            path={`/admin/process-groups/${processGroup.id}`}
          />
        </ul>
      </>
    );
  }
  return null;
}

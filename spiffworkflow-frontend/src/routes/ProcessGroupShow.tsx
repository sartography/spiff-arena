import { useEffect, useState } from 'react';
import { Link, useSearchParams, useParams } from 'react-router-dom';
// @ts-ignore
import { Button, Table, Stack } from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import {
  getPageInfoFromSearchParams,
  modifyProcessModelPath,
  unModifyProcessModelPath,
} from '../helpers';
import {
  PaginationObject,
  PermissionsToCheck,
  ProcessGroup,
  ProcessModel,
} from '../interfaces';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessGroupListTiles from '../components/ProcessGroupListTiles';

export default function ProcessGroupShow() {
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  const [processModels, setProcessModels] = useState([]);
  const [modelPagination, setModelPagination] =
    useState<PaginationObject | null>(null);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processGroupListPath]: ['POST'],
    [targetUris.processGroupShowPath]: ['PUT'],
    [targetUris.processModelCreatePath]: ['POST'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  useEffect(() => {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);

    const setProcessModelFromResult = (result: any) => {
      setProcessModels(result.results);
      setModelPagination(result.pagination);
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
        <h2>Process Models</h2>
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

  if (processGroup && modelPagination) {
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
        <h1>Process Group: {processGroup.display_name}</h1>
        <ul>
          <Stack orientation="horizontal" gap={3}>
            <Can I="POST" a={targetUris.processGroupListPath} ability={ability}>
              <Button
                href={`/admin/process-groups/new?parentGroupId=${processGroup.id}`}
              >
                Add a process group
              </Button>
            </Can>
            <Can
              I="POST"
              a={targetUris.processModelCreatePath}
              ability={ability}
            >
              <Button
                href={`/admin/process-models/${modifiedProcessGroupId}/new`}
              >
                Add a process model
              </Button>
            </Can>
            <Can I="PUT" a={targetUris.processGroupShowPath} ability={ability}>
              <Button
                href={`/admin/process-groups/${modifiedProcessGroupId}/edit`}
              >
                Edit process group
              </Button>
            </Can>
          </Stack>
          <br />
          <br />
          {/* eslint-disable-next-line sonarjs/no-gratuitous-expressions */}
          {modelPagination && modelPagination.total > 0 && (
            <PaginationForTable
              page={page}
              perPage={perPage}
              pagination={modelPagination}
              tableToDisplay={buildModelTable()}
            />
          )}
          <br />
          <br />
          <ProcessGroupListTiles
            processGroup={processGroup}
            headerElement={<h2>Process Groups</h2>}
          />
        </ul>
      </>
    );
  }
  return null;
}

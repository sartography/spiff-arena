import { useEffect, useState } from 'react';
import {
  // Link,
  useSearchParams,
  useParams,
  useNavigate,
} from 'react-router-dom';
import {
  TrashCan,
  Edit,
  // @ts-ignore
} from '@carbon/icons-react';
// @ts-ignore
import { Button, Stack } from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';
import {
  PaginationObject,
  PermissionsToCheck,
  ProcessGroup,
  // ProcessModel,
} from '../interfaces';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessGroupListTiles from '../components/ProcessGroupListTiles';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import ProcessModelListTiles from '../components/ProcessModelListTiles';

export default function ProcessGroupShow() {
  const params = useParams();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processGroup, setProcessGroup] = useState<ProcessGroup | null>(null);
  // const [processModels, setProcessModels] = useState([]);
  const [modelPagination, setModelPagination] =
    useState<PaginationObject | null>(null);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processGroupListPath]: ['POST'],
    [targetUris.processGroupShowPath]: ['PUT', 'DELETE'],
    [targetUris.processModelCreatePath]: ['POST'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  useEffect(() => {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);

    const setProcessModelFromResult = (result: any) => {
      // setProcessModels(result.results);
      setModelPagination(result.pagination);
    };
    const processResult = (result: any) => {
      setProcessGroup(result);
      setPageTitle([result.display_name]);
      const unmodifiedProcessGroupId = unModifyProcessIdentifierForPathParam(
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

  // const buildModelTable = () => {
  //   if (processGroup === null) {
  //     return null;
  //   }
  //   const rows = processModels.map((row: ProcessModel) => {
  //     const modifiedProcessModelId: String =
  //       modifyProcessIdentifierForPathParam((row as any).id);
  //     return (
  //       <tr key={row.id}>
  //         <td>
  //           <Link
  //             to={`/process-models/${modifiedProcessModelId}`}
  //             data-qa="process-model-show-link"
  //           >
  //             {row.id}
  //           </Link>
  //         </td>
  //         <td>{row.display_name}</td>
  //       </tr>
  //     );
  //   });
  //   return (
  //     <div>
  //       <h2>Process Models</h2>
  //       <Table striped bordered>
  //         <thead>
  //           <tr>
  //             <th>Process Model Id</th>
  //             <th>Display Name</th>
  //           </tr>
  //         </thead>
  //         <tbody>{rows}</tbody>
  //       </Table>
  //     </div>
  //   );
  // };

  const navigateToProcessGroups = (_result: any) => {
    navigate(`/process-groups`);
  };

  const deleteProcessGroup = () => {
    if (processGroup) {
      HttpService.makeCallToBackend({
        path: `/process-groups/${modifyProcessIdentifierForPathParam(
          processGroup.id
        )}`,
        successCallback: navigateToProcessGroups,
        httpMethod: 'DELETE',
      });
    }
  };

  if (processGroup && modelPagination) {
    // const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    const modifiedProcessGroupId = modifyProcessIdentifierForPathParam(
      processGroup.id
    );
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: processGroup,
              entityType: 'process-group',
            },
          ]}
        />
        <Stack orientation="horizontal" gap={1}>
          <h1 className="with-icons">
            Process Group: {processGroup.display_name}
          </h1>
          <Can I="PUT" a={targetUris.processGroupShowPath} ability={ability}>
            <Button
              kind="ghost"
              data-qa="edit-process-group-button"
              renderIcon={Edit}
              iconDescription="Edit Process Group"
              hasIconOnly
              href={`/process-groups/${modifiedProcessGroupId}/edit`}
            >
              Edit process group
            </Button>
          </Can>
          <Can I="DELETE" a={targetUris.processGroupShowPath} ability={ability}>
            <ButtonWithConfirmation
              kind="ghost"
              data-qa="delete-process-group-button"
              renderIcon={TrashCan}
              iconDescription="Delete Process Group"
              hasIconOnly
              description={`Delete process group: ${processGroup.display_name}`}
              onConfirmation={deleteProcessGroup}
              confirmButtonLabel="Delete"
            />
          </Can>
        </Stack>
        <p className="process-description">{processGroup.description}</p>
        <ul>
          <Stack orientation="horizontal" gap={3}>
            <Can I="POST" a={targetUris.processGroupListPath} ability={ability}>
              <Button
                href={`/process-groups/new?parentGroupId=${processGroup.id}`}
              >
                Add a process group
              </Button>
            </Can>
            <Can
              I="POST"
              a={targetUris.processModelCreatePath}
              ability={ability}
            >
              <Button href={`/process-models/${modifiedProcessGroupId}/new`}>
                Add a process model
              </Button>
            </Can>
          </Stack>
          <br />
          <br />
          <ProcessModelListTiles
            headerElement={<h2>Process Models</h2>}
            processGroup={processGroup}
          />
          {/* eslint-disable-next-line sonarjs/no-gratuitous-expressions */}
          {/* {modelPagination && modelPagination.total > 0 && (
            <PaginationForTable
              page={page}
              perPage={perPage}
              pagination={modelPagination}
              tableToDisplay={buildModelTable()}
            />
          )} */}
          <br />
          <br />
          <ProcessGroupListTiles
            processGroup={processGroup}
            headerElement={<h2 className="clear-left">Process Groups</h2>}
          />
        </ul>
      </>
    );
  }
  return null;
}

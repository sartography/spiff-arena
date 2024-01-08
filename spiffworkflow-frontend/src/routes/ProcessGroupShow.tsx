import { useParams, useNavigate } from 'react-router-dom';
import { TrashCan, Edit } from '@carbon/icons-react';
import { Button, Stack } from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import {
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
} from '../helpers';
import { PermissionsToCheck } from '../interfaces';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessGroupListTiles from '../components/ProcessGroupListTiles';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import ProcessModelListTiles from '../components/ProcessModelListTiles';
import useProcessGroupFetcher from '../hooks/useProcessGroupFetcher';

export default function ProcessGroupShow() {
  const params = useParams();
  const navigate = useNavigate();

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.dataStoreListPath]: ['POST'],
    [targetUris.processGroupListPath]: ['POST'],
    [targetUris.processGroupShowPath]: ['PUT', 'DELETE'],
    [targetUris.processModelCreatePath]: ['POST'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData
  );
  const unModifiedProcessGroupId = unModifyProcessIdentifierForPathParam(
    `${params.process_group_id}`
  );
  const { processGroup } = useProcessGroupFetcher(unModifiedProcessGroupId);

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

  if (processGroup && permissionsLoaded) {
    const modifiedProcessGroupId = modifyProcessIdentifierForPathParam(
      processGroup.id
    );
    const showNoItemsDisplayText =
      (processGroup.process_groups || []).length < 1 &&
      (processGroup.process_models || []).length < 1;
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
            <Can I="POST" a={targetUris.dataStoreListPath} ability={ability}>
              <Button
                href={`/data-stores/new?parentGroupId=${processGroup.id}`}
              >
                Add a data store
              </Button>
            </Can>
          </Stack>
          <br />
          <br />
          <ProcessModelListTiles
            headerElement={<h2>Process Models</h2>}
            processGroup={processGroup}
            showNoItemsDisplayText={showNoItemsDisplayText}
            userCanCreateProcessModels={ability.can(
              'POST',
              targetUris.processModelCreatePath
            )}
          />
          <br />
          <br />
          <ProcessGroupListTiles
            processGroup={processGroup}
            headerElement={<h2 className="clear-left">Process Groups</h2>}
            showNoItemsDisplayText={showNoItemsDisplayText}
            userCanCreateProcessModels={ability.can(
              'POST',
              targetUris.processGroupListPath
            )}
          />
        </ul>
      </>
    );
  }
  return null;
}

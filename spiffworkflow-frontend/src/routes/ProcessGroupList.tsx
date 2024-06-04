import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Button,
  Stack,
  // @ts-ignore
} from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import { modifyProcessIdentifierForPathParam, setPageTitle } from '../helpers';
import { CarbonComboBoxSelection, PermissionsToCheck } from '../interfaces';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessModelSearch from '../components/ProcessModelSearch';
import ProcessGroupListTiles from '../components/ProcessGroupListTiles';
import DataStoreListTiles from '../components/DataStoreListTiles';

export default function ProcessGroupList() {
  const navigate = useNavigate();

  const [processModelAvailableItems, setProcessModelAvailableItems] = useState(
    [],
  );

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.dataStoreListPath]: ['POST'],
    [targetUris.processGroupListPath]: ['POST'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  useEffect(() => {
    const processResultForProcessModels = (result: any) => {
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.id}`;
        Object.assign(item, { label });
        return item;
      });
      setProcessModelAvailableItems(selectionArray);
    };
    // for search box
    HttpService.makeCallToBackend({
      path: `/process-models?per_page=1000&recursive=true&include_parent_groups=true`,
      successCallback: processResultForProcessModels,
    });
    setPageTitle(['Process Groups']);
  }, []);

  const processModelSearchArea = () => {
    if (processModelAvailableItems.length < 1) {
      return null;
    }
    const processModelSearchOnChange = (selection: CarbonComboBoxSelection) => {
      const processModel = selection.selectedItem;
      navigate(
        `/process-models/${modifyProcessIdentifierForPathParam(
          processModel.id,
        )}`,
      );
    };
    return (
      <ProcessModelSearch
        onChange={processModelSearchOnChange}
        processModels={processModelAvailableItems}
        titleText="Process model search"
      />
    );
  };

  if (processModelAvailableItems) {
    return (
      <>
        <ProcessBreadcrumb hotCrumbs={[['Process Groups']]} />
        <Stack orientation="horizontal" gap={3}>
          <Can I="POST" a={targetUris.processGroupListPath} ability={ability}>
            <Button kind="primary" href="/process-groups/new">
              Add a process group
            </Button>
          </Can>
          <Can I="POST" a={targetUris.dataStoreListPath} ability={ability}>
            <Button href="/data-stores/new?parentGroupId=">
              Add a data store
            </Button>
          </Can>
        </Stack>
        <br />
        <br />
        {processModelSearchArea()}
        <br />
        <ProcessGroupListTiles showNoItemsDisplayText />
        <br />
        <br />
        <DataStoreListTiles
          headerElement={<h2 className="clear-left">Data Stores</h2>}
          userCanCreateDataStores={ability.can(
            'POST',
            targetUris.dataStoreListPath,
          )}
        />
      </>
    );
  }
  return null;
}

import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Button,
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

export default function ProcessGroupList() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processModelAvailableItems, setProcessModelAvailableItems] = useState(
    []
  );

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
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
  }, [searchParams]);

  const processModelSearchArea = () => {
    const processModelSearchOnChange = (selection: CarbonComboBoxSelection) => {
      const processModel = selection.selectedItem;
      navigate(
        `/process-models/${modifyProcessIdentifierForPathParam(
          processModel.id
        )}`
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
        <Can I="POST" a={targetUris.processGroupListPath} ability={ability}>
          <Button kind="secondary" href="/process-groups/new">
            Add a process group
          </Button>
          <br />
          <br />
        </Can>
        <br />
        {processModelSearchArea()}
        <br />
        <ProcessGroupListTiles />
      </>
    );
  }
  return null;
}

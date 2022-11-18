import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  ArrowRight,
  // @ts-ignore
} from '@carbon/icons-react';
import {
  Button,
  ClickableTile,
  // @ts-ignore
} from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import { modifyProcessModelPath, truncateString } from '../helpers';
import {
  CarbonComboBoxSelection,
  PermissionsToCheck,
  ProcessGroup,
} from '../interfaces';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessModelSearch from '../components/ProcessModelSearch';

// Example process group json
// {'process_group_id': 'sure', 'display_name': 'Test Workflows', 'id': 'test_process_group'}
export default function ProcessGroupList() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const [processGroups, setProcessGroups] = useState<ProcessGroup[] | null>(
    null
  );
  const [processModelAvailableItems, setProcessModelAvailableItems] = useState(
    []
  );

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processGroupListPath]: ['POST'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  useEffect(() => {
    const setProcessGroupsFromResult = (result: any) => {
      setProcessGroups(result.results);
    };
    const processResultForProcessModels = (result: any) => {
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.id}`;
        Object.assign(item, { label });
        return item;
      });
      setProcessModelAvailableItems(selectionArray);
    };

    // for browsing
    HttpService.makeCallToBackend({
      path: `/process-groups?per_page=1000`,
      successCallback: setProcessGroupsFromResult,
    });
    // for search box
    HttpService.makeCallToBackend({
      path: `/process-models?per_page=1000`,
      successCallback: processResultForProcessModels,
    });
  }, [searchParams]);

  const processGroupDirectChildrenCount = (processGroup: ProcessGroup) => {
    return (
      (processGroup.process_models || []).length +
      (processGroup.process_groups || []).length
    );
  };

  const processGroupsDisplayArea = () => {
    let displayText = null;
    if (processGroups && processGroups.length > 0) {
      displayText = (processGroups || []).map((row: ProcessGroup) => {
        return (
          <ClickableTile
            id="tile-1"
            className="tile-process-group"
            href={`/admin/process-groups/${row.id}`}
          >
            <div className="tile-process-group-content-container">
              <ArrowRight />
              <div className="tile-process-group-display-name">
                {row.display_name}
              </div>
              <p className="tile-process-group-description">
                {truncateString(row.description || '', 25)}
              </p>
              <p className="tile-process-group-children-count">
                Total Sub Items: {processGroupDirectChildrenCount(row)}
              </p>
            </div>
          </ClickableTile>
        );
      });
    } else {
      displayText = <p>No Groups To Display</p>;
    }
    return displayText;
  };

  const processModelSearchArea = () => {
    const processModelSearchOnChange = (selection: CarbonComboBoxSelection) => {
      const processModel = selection.selectedItem;
      navigate(
        `/admin/process-models/${modifyProcessModelPath(processModel.id)}`
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

  if (processGroups) {
    return (
      <>
        <ProcessBreadcrumb hotCrumbs={[['Process Groups']]} />
        <Can I="POST" a={targetUris.processGroupListPath} ability={ability}>
          <Button kind="secondary" href="/admin/process-groups/new">
            Add a process group
          </Button>
          <br />
          <br />
        </Can>
        <br />
        {processModelSearchArea()}
        <br />
        {processGroupsDisplayArea()}
      </>
    );
  }
  return null;
}

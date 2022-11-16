import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Button,
  Table,
  // @ts-ignore
} from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import {
  getPageInfoFromSearchParams,
  modifyProcessModelPath,
} from '../helpers';
import {
  CarbonComboBoxSelection,
  PermissionsToCheck,
  ProcessGroup,
} from '../interfaces';
import ProcessModelSearch from '../components/ProcessModelSearch';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { usePermissionFetcher } from '../hooks/PermissionService';

// Example process group json
// {'process_group_id': 'sure', 'display_name': 'Test Workflows', 'id': 'test_process_group'}
export default function ProcessGroupList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [processGroups, setProcessGroups] = useState([]);
  const [pagination, setPagination] = useState(null);
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
      setPagination(result.pagination);
    };
    const processResultForProcessModels = (result: any) => {
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.id}`;
        Object.assign(item, { label });
        return item;
      });
      setProcessModelAvailableItems(selectionArray);
    };

    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    // for browsing
    HttpService.makeCallToBackend({
      path: `/process-groups?per_page=${perPage}&page=${page}`,
      successCallback: setProcessGroupsFromResult,
    });
    // for search box
    HttpService.makeCallToBackend({
      path: `/process-models?per_page=1000`,
      successCallback: processResultForProcessModels,
    });
  }, [searchParams]);

  const buildTable = () => {
    const rows = processGroups.map((row: ProcessGroup) => {
      return (
        <tr key={(row as any).id}>
          <td>
            <Link
              to={`/admin/process-groups/${(row as any).id}`}
              title={(row as any).id}
            >
              {(row as any).display_name}
            </Link>
          </td>
        </tr>
      );
    });
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Process Group</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const processGroupsDisplayArea = () => {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    let displayText = null;
    if (processGroups?.length > 0) {
      displayText = (
        <>
          <h3>Browse</h3>
          <PaginationForTable
            page={page}
            perPage={perPage}
            pagination={pagination as any}
            tableToDisplay={buildTable()}
          />
        </>
      );
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

  if (pagination) {
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
        {processModelSearchArea()}
        <br />
        {processGroupsDisplayArea()}
      </>
    );
  }
  return null;
}

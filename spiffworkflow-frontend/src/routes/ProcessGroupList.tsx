import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import {
  Button,
  Table,
  // ExpandableTile,
  // TileAboveTheFoldContent,
  // TileBelowTheFoldContent,
  // TextInput,
  // ClickableTile,
  // @ts-ignore
} from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import { getPageInfoFromSearchParams } from '../helpers';
import { CarbonComboBoxSelection, ProcessGroup } from '../interfaces';
import ProcessModelSearch from '../components/ProcessModelSearch';

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

  useEffect(() => {
    const setProcessGroupsFromResult = (result: any) => {
      setProcessGroups(result.results);
      setPagination(result.pagination);
    };
    const processResultForProcessModels = (result: any) => {
      const selectionArray = result.results.map((item: any) => {
        const label = `${item.process_group_id}/${item.id}`;
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
    // const rows = processGroups.map((row: ProcessGroup) => {
    //   return (
    //     <span>
    //       <ClickableTile href={`/admin/process-groups/${row.id}`}>
    //         {row.display_name}
    //       </ClickableTile>
    //     </span>
    //   );
    // });
    //
    // return <div style={{ width: '400px' }}>{rows}</div>;
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
            path="/admin/process-groups"
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
        `/admin/process-models/${processModel.process_group_id}/${processModel.id}`
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
        <Button kind="secondary" href="/admin/process-groups/new">
          Add a process group
        </Button>
        <br />
        <br />
        {processModelSearchArea()}
        <br />
        {processGroupsDisplayArea()}
      </>
    );
  }
  return null;
}

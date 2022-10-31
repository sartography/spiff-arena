import { useEffect, useState } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { Button, Form, Table } from '@carbon/react';
import { InputGroup } from 'react-bootstrap';
import { Typeahead } from 'react-bootstrap-typeahead';
import { Option } from 'react-bootstrap-typeahead/types/types';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import PaginationForTable from '../components/PaginationForTable';
import HttpService from '../services/HttpService';
import { getPageInfoFromSearchParams } from '../helpers';
import { ProcessModel } from '../interfaces';

// Example process group json
// {'process_group_id': 'sure', 'display_name': 'Test Workflows', 'id': 'test_process_group'}
export default function ProcessGroupList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  const [processGroups, setProcessGroups] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [processModeleSelectionOptions, setProcessModelSelectionOptions] =
    useState([]);

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
      setProcessModelSelectionOptions(selectionArray);
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
    const rows = processGroups.map((row) => {
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
    const processModelSearchOnChange = (selected: Option[]) => {
      const processModel = selected[0] as ProcessModel;
      navigate(
        `/admin/process-models/${processModel.process_group_id}/${processModel.id}`
      );
    };
    return (
      <form onSubmit={function hey() {}}>
        <h3>Search</h3>
        <Form.Group>
          <InputGroup>
            <InputGroup.Text className="text-nowrap">
              Process Model:{' '}
            </InputGroup.Text>
            <Typeahead
              style={{ width: 500 }}
              id="process-model-selection"
              labelKey="label"
              onChange={processModelSearchOnChange}
              // for cypress tests since data-qa does not work
              inputProps={{
                name: 'process-model-selection',
              }}
              options={processModeleSelectionOptions}
              placeholder="Choose a process model..."
            />
          </InputGroup>
        </Form.Group>
      </form>
    );
  };

  if (pagination) {
    return (
      <>
        <ProcessBreadcrumb hotCrumbs={[['Process Groups']]} />
        <Button href="/admin/process-groups/new">Add a process group</Button>
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

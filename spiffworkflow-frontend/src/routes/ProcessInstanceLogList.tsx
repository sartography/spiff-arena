import { useEffect, useState } from 'react';
// @ts-ignore
import { Table, Tabs, TabList, Tab } from '@carbon/react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import PaginationForTable from '../components/PaginationForTable';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  convertSecondsToFormattedDateTime,
} from '../helpers';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';

export default function ProcessInstanceLogList() {
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [processInstanceLogs, setProcessInstanceLogs] = useState([]);
  const [pagination, setPagination] = useState(null);
  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    `${params.process_model_id}`
  );
  const { targetUris } = useUriListForPermissions();
  const isDetailedView = searchParams.get('detailed') === 'true';

  useEffect(() => {
    const setProcessInstanceLogListFromResult = (result: any) => {
      setProcessInstanceLogs(result.results);
      setPagination(result.pagination);
    };
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceLogListPath}?per_page=${perPage}&page=${page}&detailed=${isDetailedView}`,
      successCallback: setProcessInstanceLogListFromResult,
    });
  }, [
    searchParams,
    params,
    targetUris.processInstanceLogListPath,
    isDetailedView,
  ]);

  const buildTable = () => {
    const rows = processInstanceLogs.map((row) => {
      const rowToUse = row as any;
      return (
        <tr key={rowToUse.id}>
          <td data-qa="paginated-entity-id">{rowToUse.id}</td>
          <td>{rowToUse.bpmn_task_name}</td>
          {isDetailedView && (
            <>
              <td>{rowToUse.message}</td>
              <td>{rowToUse.bpmn_task_identifier}</td>
              <td>{rowToUse.bpmn_task_type}</td>
              <td>{rowToUse.bpmn_process_identifier}</td>
            </>
          )}
          <td>{rowToUse.username}</td>
          <td>
            <Link
              data-qa="process-instance-show-link"
              to={`/admin/process-instances/${modifiedProcessModelId}/${rowToUse.process_instance_id}/${rowToUse.spiff_step}`}
            >
              {convertSecondsToFormattedDateTime(rowToUse.timestamp)}
            </Link>
          </td>
        </tr>
      );
    });
    return (
      <Table size="lg">
        <thead>
          <tr>
            <th>Id</th>
            <th>Task Name</th>
            {isDetailedView && (
              <>
                <th>Message</th>
                <th>Task Identifier</th>
                <th>Task Type</th>
                <th>Bpmn Process Identifier</th>
              </>
            )}
            <th>User</th>
            <th>Timestamp</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };
  const selectedTabIndex = isDetailedView ? 1 : 0;

  if (pagination) {
    const { page, perPage } = getPageInfoFromSearchParams(searchParams);
    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            {
              entityToExplode: params.process_model_id || '',
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [
              `Process Instance: ${params.process_instance_id}`,
              `/admin/process-instances/${params.process_model_id}/${params.process_instance_id}`,
            ],
            ['Logs'],
          ]}
        />
        <Tabs selectedIndex={selectedTabIndex}>
          <TabList aria-label="List of tabs">
            <Tab
              title="Only show a subset of the logs, and show fewer columns"
              data-qa="process-instance-log-simple"
              onClick={() => {
                searchParams.set('detailed', 'false');
                setSearchParams(searchParams);
              }}
            >
              Simple
            </Tab>
            <Tab
              title="Show all logs for this process instance, and show extra columns that may be useful for debugging"
              data-qa="process-instance-log-detailed"
              onClick={() => {
                searchParams.set('detailed', 'true');
                setSearchParams(searchParams);
              }}
            >
              Detailed
            </Tab>
          </TabList>
        </Tabs>
        <br />
        <PaginationForTable
          page={page}
          perPage={perPage}
          pagination={pagination}
          tableToDisplay={buildTable()}
        />
      </>
    );
  }
  return null;
}

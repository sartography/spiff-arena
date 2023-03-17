import { useEffect, useState } from 'react';
// @ts-ignore
import { Table, Tabs, TabList, Tab } from '@carbon/react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import PaginationForTable from '../components/PaginationForTable';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import {
  getPageInfoFromSearchParams,
  convertSecondsToFormattedDateTime,
} from '../helpers';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceLogList({ variant }: OwnProps) {
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [processInstanceLogs, setProcessInstanceLogs] = useState([]);
  const [pagination, setPagination] = useState(null);
  const { targetUris } = useUriListForPermissions();
  const isDetailedView = searchParams.get('detailed') === 'true';

  let processInstanceShowPageBaseUrl = `/admin/process-instances/for-me/${params.process_model_id}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = `/admin/process-instances/${params.process_model_id}`;
  }

  useEffect(() => {
    // Clear out any previous results to avoid a "flicker" effect where columns
    // are updated above the incorrect data.
    setProcessInstanceLogs([]);
    setPagination(null);

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

  const getTableRow = (row: any) => {
    const tableRow = [];
    const taskNameCell = (
      <td>
        {row.task_definition_name ||
          (row.bpmn_task_type === 'StartEvent' ? 'Process Started' : '') ||
          (row.bpmn_task_type === 'EndEvent' ? 'Process Ended' : '')}
      </td>
    );
    const bpmnProcessCell = (
      <td>
        {row.bpmn_process_definition_name ||
          row.bpmn_process_definition_identifier}
      </td>
    );
    if (isDetailedView) {
      tableRow.push(
        <>
          <td data-qa="paginated-entity-id">{row.id}</td>
          {bpmnProcessCell}
          {taskNameCell}
        </>
      );
    } else {
      tableRow.push(
        <>
          {taskNameCell}
          {bpmnProcessCell}
        </>
      );
    }
    if (isDetailedView) {
      tableRow.push(
        <>
          <td>{row.bpmn_task_type}</td>
          <td>{row.event_type}</td>
          <td>
            {row.username || (
              <span className="system-user-log-entry">system</span>
            )}
          </td>
        </>
      );
    }
    tableRow.push(
      <td>
        <Link
          data-qa="process-instance-show-link"
          to={`${processInstanceShowPageBaseUrl}/${row.process_instance_id}/${row.spiff_step}`}
        >
          {convertSecondsToFormattedDateTime(row.timestamp)}
        </Link>
      </td>
    );
    return <tr key={row.id}>{tableRow}</tr>;
  };

  const buildTable = () => {
    const rows = processInstanceLogs.map((row) => {
      return getTableRow(row);
    });

    const tableHeaders = [];
    if (isDetailedView) {
      tableHeaders.push(
        <>
          <th>Id</th>
          <th>Bpmn Process</th>
          <th>Task Name</th>
        </>
      );
    } else {
      tableHeaders.push(
        <>
          <th>Event</th>
          <th>Bpmn Process</th>
        </>
      );
    }
    if (isDetailedView) {
      tableHeaders.push(
        <>
          <th>Task Type</th>
          <th>Event</th>
          <th>User</th>
        </>
      );
    }
    tableHeaders.push(<th>Timestamp</th>);
    return (
      <Table size="lg">
        <thead>
          <tr>{tableHeaders}</tr>
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
              `${processInstanceShowPageBaseUrl}/${params.process_instance_id}`,
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
              Milestones
            </Tab>
            <Tab
              title="Show all logs for this process instance, and show extra columns that may be useful for debugging"
              data-qa="process-instance-log-detailed"
              onClick={() => {
                searchParams.set('detailed', 'true');
                setSearchParams(searchParams);
              }}
            >
              Events
            </Tab>
            {/*
              Suspend
              Resumed
              Terminated

              Skipped?
              Rewind?
              Execute?
              Edit?
            */}
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

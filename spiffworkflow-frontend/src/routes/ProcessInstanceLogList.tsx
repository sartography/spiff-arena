import { useEffect, useState } from 'react';
import {
  Table,
  Tabs,
  TabList,
  Tab,
  Grid,
  Column,
  ButtonSet,
  Button,
  TextInput,
  ComboBox,
  // @ts-ignore
} from '@carbon/react';
import {
  createSearchParams,
  Link,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import { useDebouncedCallback } from 'use-debounce';
import PaginationForTable from '../components/PaginationForTable';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import {
  getPageInfoFromSearchParams,
  convertSecondsToFormattedDateTime,
  selectKeysFromSearchParams,
} from '../helpers';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import { ProcessInstanceLogEntry } from '../interfaces';
import Filters from '../components/Filters';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceLogList({ variant }: OwnProps) {
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const [processInstanceLogs, setProcessInstanceLogs] = useState([]);
  const [pagination, setPagination] = useState(null);

  const [taskName, setTaskName] = useState<string>('');
  const [taskIdentifier, setTaskIdentifier] = useState<string>('');

  const [taskTypes, setTaskTypes] = useState<string[]>([]);
  const [eventTypes, setEventTypes] = useState<string[]>([]);

  const { targetUris } = useUriListForPermissions();
  const isDetailedView = searchParams.get('detailed') === 'true';

  const taskNameHeader = isDetailedView ? 'Task Name' : 'Milestone';

  const [showFilterOptions, setShowFilterOptions] = useState<boolean>(false);

  let processInstanceShowPageBaseUrl = `/admin/process-instances/for-me/${params.process_model_id}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = `/admin/process-instances/${params.process_model_id}`;
  }

  const updateSearchParams = (value: string, key: string) => {
    if (value) {
      searchParams.set(key, value);
    } else {
      searchParams.delete(key);
    }
    setSearchParams(searchParams);
  };

  const addDebouncedSearchParams = useDebouncedCallback(
    (value: string, key: string) => {
      updateSearchParams(value, key);
    },
    // delay in ms
    1000
  );

  useEffect(() => {
    // Clear out any previous results to avoid a "flicker" effect where columns
    // are updated above the incorrect data.
    setProcessInstanceLogs([]);
    setPagination(null);

    const setProcessInstanceLogListFromResult = (result: any) => {
      setProcessInstanceLogs(result.results);
      setPagination(result.pagination);
    };

    const searchParamsToInclude = [
      'detailed',
      'page',
      'per_page',
      'bpmn_name',
      'bpmn_identifier',
      'task_type',
      'event_type',
    ];
    const pickedSearchParams = selectKeysFromSearchParams(
      searchParams,
      searchParamsToInclude
    );

    if ('bpmn_name' in pickedSearchParams) {
      setTaskName(pickedSearchParams.bpmn_name);
    }
    if ('bpmn_identifier' in pickedSearchParams) {
      setTaskIdentifier(pickedSearchParams.bpmn_identifier);
    }

    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceLogListPath}?${createSearchParams(
        pickedSearchParams
      )}`,
      successCallback: setProcessInstanceLogListFromResult,
    });
    HttpService.makeCallToBackend({
      path: `/v1.0/logs/types`,
      successCallback: (result: any) => {
        setTaskTypes(result.task_types);
        setEventTypes(result.event_types);
      },
    });
  }, [
    searchParams,
    params,
    targetUris.processInstanceLogListPath,
    isDetailedView,
  ]);

  const getTableRow = (logEntry: ProcessInstanceLogEntry) => {
    const tableRow = [];
    const taskNameCell = (
      <td>
        {logEntry.task_definition_name ||
          (logEntry.bpmn_task_type === 'StartEvent' ? 'Process Started' : '') ||
          (logEntry.bpmn_task_type === 'EndEvent' ? 'Process Ended' : '')}
      </td>
    );
    const bpmnProcessCell = (
      <td>
        {logEntry.bpmn_process_definition_name ||
          logEntry.bpmn_process_definition_identifier}
      </td>
    );
    if (isDetailedView) {
      tableRow.push(
        <>
          <td data-qa="paginated-entity-id">{logEntry.id}</td>
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
          <td>{logEntry.task_definition_identifier}</td>
          <td>{logEntry.bpmn_task_type}</td>
          <td>{logEntry.event_type}</td>
          <td>
            {logEntry.username || (
              <span className="system-user-log-entry">system</span>
            )}
          </td>
        </>
      );
    }

    let timestampComponent = (
      <td>{convertSecondsToFormattedDateTime(logEntry.timestamp)}</td>
    );
    if (logEntry.spiff_task_guid) {
      timestampComponent = (
        <td>
          <Link
            data-qa="process-instance-show-link"
            to={`${processInstanceShowPageBaseUrl}/${logEntry.process_instance_id}/${logEntry.spiff_task_guid}`}
            title="View state when task was completed"
          >
            {convertSecondsToFormattedDateTime(logEntry.timestamp)}
          </Link>
        </td>
      );
    }
    tableRow.push(timestampComponent);

    return <tr key={logEntry.id}>{tableRow}</tr>;
  };

  const buildTable = () => {
    const rows = processInstanceLogs.map(
      (logEntry: ProcessInstanceLogEntry) => {
        return getTableRow(logEntry);
      }
    );

    const tableHeaders = [];
    if (isDetailedView) {
      tableHeaders.push(
        <>
          <th>Id</th>
          <th>Bpmn Process</th>
          <th>{taskNameHeader}</th>
        </>
      );
    } else {
      tableHeaders.push(
        <>
          <th>{taskNameHeader}</th>
          <th>Bpmn Process</th>
        </>
      );
    }
    if (isDetailedView) {
      tableHeaders.push(
        <>
          <th>Task Identifier</th>
          <th>Task Type</th>
          <th>Event Type</th>
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

  const resetFilters = () => {
    setTaskIdentifier('');
    setTaskName('');

    ['bpmn_name', 'bpmn_identifier', 'task_type', 'event_type'].forEach(
      (value: string) => searchParams.delete(value)
    );

    setSearchParams(searchParams);
  };

  const shouldFilterStringItem = (options: any) => {
    const stringItem = options.item;
    let { inputValue } = options;
    if (!inputValue) {
      inputValue = '';
    }
    return stringItem.toLowerCase().includes(inputValue.toLowerCase());
  };

  const filterOptions = () => {
    if (!showFilterOptions) {
      return null;
    }

    const filterElements = [];
    filterElements.push(
      <Column md={4}>
        <TextInput
          id="task-name-filter"
          labelText={taskNameHeader}
          value={taskName}
          onChange={(event: any) => {
            const newValue = event.target.value;
            setTaskName(newValue);
            addDebouncedSearchParams(newValue, 'bpmn_name');
          }}
        />
      </Column>
    );

    if (isDetailedView) {
      filterElements.push(
        <>
          <Column md={4}>
            <TextInput
              id="task-identifier-filter"
              labelText="Task Identifier"
              value={taskIdentifier}
              onChange={(event: any) => {
                const newValue = event.target.value;
                setTaskIdentifier(newValue);
                addDebouncedSearchParams(newValue, 'bpmn_identifier');
              }}
            />
          </Column>
          <Column md={4}>
            <ComboBox
              onChange={(value: any) => {
                updateSearchParams(value.selectedItem, 'task_type');
              }}
              id="task-type-select"
              data-qa="task-type-select"
              items={taskTypes}
              itemToString={(value: string) => {
                return value;
              }}
              shouldFilterItem={shouldFilterStringItem}
              placeholder="Choose a process model"
              titleText="Task Type"
              selectedItem={searchParams.get('task_type')}
            />
          </Column>
          <Column md={4}>
            <ComboBox
              onChange={(value: any) => {
                updateSearchParams(value.selectedItem, 'event_type');
              }}
              id="event-type-select"
              data-qa="event-type-select"
              items={eventTypes}
              itemToString={(value: string) => {
                return value;
              }}
              shouldFilterItem={shouldFilterStringItem}
              placeholder="Choose a process model"
              titleText="Event Type"
              selectedItem={searchParams.get('event_type')}
            />
          </Column>
        </>
      );
    }

    return (
      <>
        <Grid fullWidth className="with-bottom-margin">
          {filterElements}
        </Grid>
        <Grid fullWidth className="with-bottom-margin">
          <Column sm={4} md={4} lg={8}>
            <ButtonSet>
              <Button
                kind=""
                className="button-white-background narrow-button"
                onClick={resetFilters}
              >
                Reset
              </Button>
            </ButtonSet>
          </Column>
        </Grid>
      </>
    );
  };

  const tabs = () => {
    const selectedTabIndex = isDetailedView ? 1 : 0;
    return (
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
        </TabList>
      </Tabs>
    );
  };

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
      {tabs()}
      <Filters
        filterOptions={filterOptions}
        showFilterOptions={showFilterOptions}
        setShowFilterOptions={setShowFilterOptions}
        filtersEnabled
      />
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

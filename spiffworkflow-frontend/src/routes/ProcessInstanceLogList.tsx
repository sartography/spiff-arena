import { useEffect, useState } from 'react';
import { ErrorOutline } from '@carbon/icons-react';
import {
  Table,
  Tabs,
  TabList,
  Tab,
  Grid,
  Column,
  ButtonSet,
  Button,
  ComboBox,
  Modal,
  Loading,
  // @ts-ignore
} from '@carbon/react';
import {
  createSearchParams,
  Link,
  useParams,
  useSearchParams,
} from 'react-router-dom';
import PaginationForTable from '../components/PaginationForTable';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import {
  getPageInfoFromSearchParams,
  convertSecondsToFormattedDateTime,
  selectKeysFromSearchParams,
} from '../helpers';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  PermissionsToCheck,
  ProcessInstanceEventErrorDetail,
  ProcessInstanceLogEntry,
} from '../interfaces';
import Filters from '../components/Filters';
import { usePermissionFetcher } from '../hooks/PermissionService';
import {
  childrenForErrorObject,
  errorForDisplayFromProcessInstanceErrorDetail,
} from '../components/ErrorDisplay';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceLogList({ variant }: OwnProps) {
  const params = useParams();
  const [clearAll, setClearAll] = useState<boolean>(false);
  const [searchParams, setSearchParams] = useSearchParams();
  const [processInstanceLogs, setProcessInstanceLogs] = useState<
    ProcessInstanceLogEntry[]
  >([]);
  const [pagination, setPagination] = useState(null);

  const [taskTypes, setTaskTypes] = useState<string[]>([]);
  const [eventTypes, setEventTypes] = useState<string[]>([]);
  const [taskBpmnNames, setTaskBpmnNames] = useState<string[]>([]);
  const [taskBpmnIdentifiers, setTaskBpmnIdentifiers] = useState<string[]>([]);

  const [eventForModal, setEventForModal] =
    useState<ProcessInstanceLogEntry | null>(null);
  const [eventErrorDetails, setEventErrorDetails] =
    useState<ProcessInstanceEventErrorDetail | null>(null);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processInstanceErrorEventDetails]: ['GET'],
  };
  const { ability } = usePermissionFetcher(permissionRequestData);

  const [showFilterOptions, setShowFilterOptions] = useState<boolean>(false);
  const randomNumberBetween0and1 = Math.random();

  let shouldDisplayClearButton = false;
  if (randomNumberBetween0and1 < 0.05) {
    // 5% chance of being here
    shouldDisplayClearButton = true;
  }

  let processInstanceShowPageBaseUrl = `/admin/process-instances/for-me/${params.process_model_id}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = `/admin/process-instances/${params.process_model_id}`;
  }
  const isEventsView = searchParams.get('events') === 'true';
  const taskNameHeader = isEventsView ? 'Task Name' : 'Milestone';

  const updateSearchParams = (value: string, key: string) => {
    if (value) {
      searchParams.set(key, value);
    } else {
      searchParams.delete(key);
    }
    setSearchParams(searchParams);
  };

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
      'events',
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

    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceLogListPath}?${createSearchParams(
        pickedSearchParams
      )}`,
      successCallback: setProcessInstanceLogListFromResult,
    });

    let typeaheadQueryParamString = '';
    if (!isEventsView) {
      typeaheadQueryParamString = '?task_type=IntermediateThrowEvent';
    }
    HttpService.makeCallToBackend({
      path: `/v1.0/logs/typeahead-filter-values/${params.process_model_id}/${params.process_instance_id}${typeaheadQueryParamString}`,
      successCallback: (result: any) => {
        setTaskTypes(result.task_types);
        setEventTypes(result.event_types);
        setTaskBpmnNames(result.task_bpmn_names);
        setTaskBpmnIdentifiers(result.task_bpmn_identifiers);
      },
    });
  }, [
    searchParams,
    params,
    targetUris.processInstanceLogListPath,
    isEventsView,
  ]);

  const handleErrorEventModalClose = () => {
    setEventForModal(null);
    setEventErrorDetails(null);
  };

  const errorEventModal = () => {
    if (eventForModal) {
      const modalHeading = 'Event Error Details';
      let errorMessageTag = (
        <Loading className="some-class" withOverlay={false} small />
      );
      if (eventErrorDetails) {
        const errorForDisplay = errorForDisplayFromProcessInstanceErrorDetail(
          eventForModal,
          eventErrorDetails
        );
        const errorChildren = childrenForErrorObject(errorForDisplay);
        // eslint-disable-next-line react/jsx-no-useless-fragment
        errorMessageTag = <>{errorChildren}</>;
      }
      return (
        <Modal
          open={!!eventForModal}
          passiveModal
          onRequestClose={handleErrorEventModalClose}
          modalHeading={modalHeading}
          modalLabel="Error Details"
        >
          {errorMessageTag}
        </Modal>
      );
    }
    return null;
  };

  const handleErrorDetailsReponse = (
    results: ProcessInstanceEventErrorDetail
  ) => {
    setEventErrorDetails(results);
  };

  const getErrorDetailsForEvent = (logEntry: ProcessInstanceLogEntry) => {
    setEventForModal(logEntry);
    if (ability.can('GET', targetUris.processInstanceErrorEventDetails)) {
      HttpService.makeCallToBackend({
        path: `${targetUris.processInstanceErrorEventDetails}/${logEntry.id}`,
        httpMethod: 'GET',
        successCallback: handleErrorDetailsReponse,
        failureCallback: (error: any) => {
          const errorObject: ProcessInstanceEventErrorDetail = {
            id: 0,
            message: `ERROR retrieving error details: ${error.message}`,
            stacktrace: [],
          };
          setEventErrorDetails(errorObject);
        },
      });
    } else {
      const notAuthorized: ProcessInstanceEventErrorDetail = {
        id: 0,
        message: 'You are not authorized to view error details',
        stacktrace: [],
      };
      setEventErrorDetails(notAuthorized);
    }
  };

  const eventTypeCell = (logEntry: ProcessInstanceLogEntry) => {
    if (
      ['process_instance_error', 'task_failed'].includes(logEntry.event_type)
    ) {
      const errorTitle = 'Event has an error';
      const errorIcon = (
        <>
          &nbsp;
          <ErrorOutline className="red-icon" />
        </>
      );
      return (
        <Button
          kind="ghost"
          className="button-link"
          onClick={() => getErrorDetailsForEvent(logEntry)}
          title={errorTitle}
        >
          {logEntry.event_type}
          {errorIcon}
        </Button>
      );
    }
    return logEntry.event_type;
  };

  const getTableRow = (logEntry: ProcessInstanceLogEntry) => {
    const tableRow = [];
    const taskNameCell = <td>{logEntry.task_definition_name}</td>;
    const bpmnProcessCell = (
      <td>
        {logEntry.bpmn_process_definition_name ||
          logEntry.bpmn_process_definition_identifier}
      </td>
    );
    if (isEventsView) {
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
    if (isEventsView) {
      tableRow.push(
        <>
          <td>{logEntry.task_definition_identifier}</td>
          <td>{logEntry.bpmn_task_type}</td>
          <td>{eventTypeCell(logEntry)}</td>
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
    if (isEventsView) {
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
    if (isEventsView) {
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
    ['bpmn_name', 'bpmn_identifier', 'task_type', 'event_type'].forEach(
      (value: string) => searchParams.delete(value)
    );
  };

  const resetFiltersAndRun = () => {
    resetFilters();
    setSearchParams(searchParams);
  };

  const clearFilters = () => {
    setClearAll(true);
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
    let taskNameFilterPlaceholder = 'Choose a milestone';
    if (isEventsView) {
      taskNameFilterPlaceholder = 'Choose a task bpmn name';
    }
    filterElements.push(
      <Column md={4}>
        <ComboBox
          onChange={(value: any) => {
            updateSearchParams(value.selectedItem, 'bpmn_name');
          }}
          id="task-name-filter"
          data-qa="task-type-select"
          items={taskBpmnNames}
          itemToString={(value: string) => {
            return value;
          }}
          shouldFilterItem={shouldFilterStringItem}
          placeholder={taskNameFilterPlaceholder}
          titleText={taskNameHeader}
          selectedItem={searchParams.get('bpmn_name')}
        />
      </Column>
    );

    if (isEventsView) {
      filterElements.push(
        <>
          <Column md={4}>
            <ComboBox
              onChange={(value: any) => {
                updateSearchParams(value.selectedItem, 'bpmn_identifier');
              }}
              id="task-identifier-filter"
              data-qa="task-type-select"
              items={taskBpmnIdentifiers}
              itemToString={(value: string) => {
                return value;
              }}
              shouldFilterItem={shouldFilterStringItem}
              placeholder="Choose a task bpmn identifier"
              titleText="Task Identifier"
              selectedItem={searchParams.get('bpmn_identifier')}
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
              placeholder="Choose a task type"
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
              placeholder="Choose an event type"
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
                onClick={resetFiltersAndRun}
              >
                Reset
              </Button>
              {shouldDisplayClearButton && (
                <Button
                  kind=""
                  className="button-white-background narrow-button"
                  onClick={clearFilters}
                >
                  Clear
                </Button>
              )}
            </ButtonSet>
          </Column>
        </Grid>
      </>
    );
  };

  const tabs = () => {
    const selectedTabIndex = isEventsView ? 1 : 0;
    return (
      <Tabs selectedIndex={selectedTabIndex}>
        <TabList aria-label="List of tabs">
          <Tab
            title="Only show a subset of the logs, and show fewer columns"
            data-qa="process-instance-log-milestones"
            onClick={() => {
              resetFilters();
              searchParams.set('events', 'false');
              setSearchParams(searchParams);
            }}
          >
            Milestones
          </Tab>
          <Tab
            title="Show all logs for this process instance, and show extra columns that may be useful for debugging"
            data-qa="process-instance-log-events"
            onClick={() => {
              resetFilters();
              searchParams.set('events', 'true');
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
  if (clearAll) {
    return <p>Page cleared 👍</p>;
  }
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
      {errorEventModal()}
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

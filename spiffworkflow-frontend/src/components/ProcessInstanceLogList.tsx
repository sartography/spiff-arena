import { useEffect, useState } from 'react';
import { ErrorOutline } from '@mui/icons-material';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Grid,
  Button,
  Modal,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
} from '@mui/material';
import { createSearchParams, Link, useSearchParams } from 'react-router-dom';
import PaginationForTable from './PaginationForTable';
import {
  getPageInfoFromSearchParams,
  selectKeysFromSearchParams,
} from '../helpers';
import HttpService from '../services/HttpService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  ObjectWithStringKeysAndValues,
  PermissionsToCheck,
  ProcessInstanceEventErrorDetail,
  ProcessInstanceLogEntry,
} from '../interfaces';
import Filters from './Filters';
import { usePermissionFetcher } from '../hooks/PermissionService';
import {
  childrenForErrorObject,
  errorForDisplayFromProcessInstanceErrorDetail,
} from './ErrorDisplay';
import DateAndTimeService from '../services/DateAndTimeService';

type OwnProps = {
  variant: string; // 'all' or 'for-me'
  isEventsView: boolean;
  processModelId: string;
  processInstanceId: number;
};

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '80%', // Increased width
  maxWidth: 'md', // Added max width for responsiveness
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
};

export default function ProcessInstanceLogList({
  variant,
  isEventsView = true,
  processModelId,
  processInstanceId,
}: OwnProps) {
  const [clearAll, setClearAll] = useState<boolean>(false);
  const [processInstanceLogs, setProcessInstanceLogs] = useState<
    ProcessInstanceLogEntry[]
  >([]);
  const [pagination, setPagination] = useState(null);
  const [searchParams, setSearchParams] = useSearchParams();

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

  let processInstanceShowPageBaseUrl = `/process-instances/for-me/${processModelId}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = `/process-instances/${processModelId}`;
  }
  const taskNameHeader = isEventsView ? 'Task name' : 'Milestone';
  const tableType = isEventsView ? 'events' : 'milestones';
  const paginationQueryParamPrefix = `log-list-${tableType}`;

  const updateSearchParams = (newValues: ObjectWithStringKeysAndValues) => {
    Object.keys(newValues).forEach((key: string) => {
      const value = newValues[key];
      if (value === undefined || value === null) {
        searchParams.delete(key);
      } else {
        searchParams.set(key, value);
      }
    });
    setSearchParams(searchParams);
  };

  const updateFilterValue = (value: string, key: string) => {
    const newValues: ObjectWithStringKeysAndValues = {};
    newValues[`${paginationQueryParamPrefix}_page`] = '1';
    newValues[key] = value;
    updateSearchParams(newValues);
  };

  useEffect(() => {
    // Clear out any previous results to avoid a "flicker" effect where columns
    // are updated above the incorrect data.
    setProcessInstanceLogs([]);

    const setProcessInstanceLogListFromResult = (result: any) => {
      setProcessInstanceLogs(result.results);
      setPagination(result.pagination);
    };

    const searchParamsToInclude = [
      'bpmn_name',
      'bpmn_identifier',
      'task_type',
      'event_type',
    ];
    const pickedSearchParams = selectKeysFromSearchParams(
      searchParams,
      searchParamsToInclude,
    );

    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix,
    );

    const eventsQueryParam = isEventsView ? 'true' : 'false';

    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceLogListPath}?${createSearchParams(
        pickedSearchParams,
      )}&page=${page}&per_page=${perPage}&events=${eventsQueryParam}`,
      successCallback: setProcessInstanceLogListFromResult,
    });

    let typeaheadQueryParamString = '';
    if (!isEventsView) {
      typeaheadQueryParamString = '?task_type=IntermediateThrowEvent';
    }
    HttpService.makeCallToBackend({
      path: `/v1.0/logs/typeahead-filter-values/${processModelId}/${processInstanceId}${typeaheadQueryParamString}`,
      successCallback: (result: any) => {
        setTaskTypes(result.task_types);
        setEventTypes(result.event_types);
        setTaskBpmnNames(result.task_bpmn_names);
        setTaskBpmnIdentifiers(result.task_bpmn_identifiers);
      },
    });
  }, [
    searchParams,
    processInstanceId,
    processModelId,
    targetUris.processInstanceLogListPath,
    isEventsView,
    paginationQueryParamPrefix,
  ]);

  const handleErrorEventModalClose = () => {
    setEventForModal(null);
    setEventErrorDetails(null);
  };

  const errorEventModal = () => {
    if (eventForModal) {
      const modalHeading = 'Event Error Details';
      let errorMessageTag = (
        <CircularProgress className="some-class" size={20} />
      );
      if (eventErrorDetails) {
        const errorForDisplay = errorForDisplayFromProcessInstanceErrorDetail(
          eventForModal,
          eventErrorDetails,
        );
        const errorChildren = childrenForErrorObject(errorForDisplay);
        // eslint-disable-next-line react/jsx-no-useless-fragment, sonarjs/jsx-no-useless-fragment
        errorMessageTag = <>{errorChildren}</>;
      }
      return (
        <Modal
          open={!!eventForModal}
          onClose={handleErrorEventModalClose}
          aria-labelledby="modal-heading"
          aria-describedby="modal-description"
        >
          <Box sx={style}>
            <h2 id="modal-heading">{modalHeading}</h2>
            <p id="modal-description">Error Details</p>
            {errorMessageTag}
          </Box>
        </Modal>
      );
    }
    return null;
  };

  const handleErrorDetailsReponse = (
    results: ProcessInstanceEventErrorDetail,
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
          variant="text"
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
    let taskName = logEntry.task_definition_name;
    if (!taskName && !isEventsView) {
      if (logEntry.bpmn_task_type === 'StartEvent') {
        taskName = 'Started';
      } else if (logEntry.bpmn_task_type === 'EndEvent') {
        taskName = 'Completed';
      }
    }
    const taskNameCell = <TableCell>{taskName}</TableCell>;
    const bpmnProcessCell = (
      <TableCell>
        {logEntry.bpmn_process_definition_name ||
          logEntry.bpmn_process_definition_identifier}
      </TableCell>
    );
    if (isEventsView) {
      tableRow.push(
        <>
          <TableCell data-qa="paginated-entity-id">{logEntry.id}</TableCell>
          {bpmnProcessCell}
          {taskNameCell}
        </>,
      );
    } else {
      tableRow.push(
        <>
          {taskNameCell}
          {bpmnProcessCell}
        </>,
      );
    }
    if (isEventsView) {
      tableRow.push(
        <>
          <TableCell>{logEntry.task_definition_identifier}</TableCell>
          <TableCell>{logEntry.bpmn_task_type}</TableCell>
          <TableCell>{eventTypeCell(logEntry)}</TableCell>
          <TableCell>
            {logEntry.username || (
              <span className="system-user-log-entry">system</span>
            )}
          </TableCell>
        </>,
      );
    }

    let timestampComponent = (
      <TableCell>
        {DateAndTimeService.convertSecondsToFormattedDateTime(
          logEntry.timestamp,
        )}
      </TableCell>
    );
    if (logEntry.spiff_task_guid && logEntry.event_type !== 'task_cancelled') {
      timestampComponent = (
        <TableCell>
          <Link
            reloadDocument
            data-qa="process-instance-show-link"
            to={`${processInstanceShowPageBaseUrl}/${logEntry.process_instance_id}/${logEntry.spiff_task_guid}`}
            title="View state when task was completed"
          >
            {DateAndTimeService.convertSecondsToFormattedDateTime(
              logEntry.timestamp,
            )}
          </Link>
        </TableCell>
      );
    }
    tableRow.push(timestampComponent);

    return <TableRow key={logEntry.id}>{tableRow}</TableRow>;
  };

  const buildTable = () => {
    const rows = processInstanceLogs.map(
      (logEntry: ProcessInstanceLogEntry) => {
        return getTableRow(logEntry);
      },
    );

    const tableHeaders = [];
    if (isEventsView) {
      tableHeaders.push(
        <>
          <TableCell>Id</TableCell>
          <TableCell>Bpmn process</TableCell>
          <TableCell>{taskNameHeader}</TableCell>
        </>,
      );
    } else {
      tableHeaders.push(
        <>
          <TableCell>{taskNameHeader}</TableCell>
          <TableCell>Bpmn process</TableCell>
        </>,
      );
    }
    if (isEventsView) {
      tableHeaders.push(
        <>
          <TableCell>Task identifier</TableCell>
          <TableCell>Task type</TableCell>
          <TableCell>Event type</TableCell>
          <TableCell>User</TableCell>
        </>,
      );
    }
    tableHeaders.push(<TableCell>Timestamp</TableCell>);
    return (
      <TableContainer>
        <Table size="medium">
          <TableHead>
            <TableRow>{tableHeaders}</TableRow>
          </TableHead>
          <TableBody>{rows}</TableBody>
        </Table>
      </TableContainer>
    );
  };

  const resetFilters = () => {
    ['bpmn_name', 'bpmn_identifier', 'task_type', 'event_type'].forEach(
      (value: string) => searchParams.delete(value),
    );
  };

  const resetFiltersAndRun = () => {
    resetFilters();
    setSearchParams(searchParams);
  };

  const clearFilters = () => {
    setClearAll(true);
  };

  const filterOptions = () => {
    if (!showFilterOptions) {
      return null;
    }

    const filterElements = [];
    if (isEventsView) {
      // taskNameFilterPlaceholder = 'Choose a task bpmn name';
    }
    filterElements.push(
      <Grid item md={4}>
        <FormControl fullWidth>
          <InputLabel id="task-name-filter-label">{taskNameHeader}</InputLabel>
          <Select
            labelId="task-name-filter-label"
            label={taskNameHeader}
            id="task-name-filter"
            value={searchParams.get('bpmn_name') || ''}
            onChange={(event) => {
              updateFilterValue(event.target.value, 'bpmn_name');
            }}
          >
            {taskBpmnNames.map((name) => (
              <MenuItem key={name} value={name}>
                {name}
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Grid>,
    );

    if (isEventsView) {
      filterElements.push(
        <>
          <Grid item md={4}>
            <FormControl fullWidth>
              <InputLabel id="task-identifier-filter-label">
                Task identifier
              </InputLabel>
              <Select
                labelId="task-identifier-filter-label"
                label="Task identifier"
                id="task-identifier-filter"
                value={searchParams.get('bpmn_identifier') || ''}
                onChange={(event) => {
                  updateFilterValue(event.target.value, 'bpmn_identifier');
                }}
              >
                {taskBpmnIdentifiers.map((identifier) => (
                  <MenuItem key={identifier} value={identifier}>
                    {identifier}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item md={4}>
            <FormControl fullWidth>
              <InputLabel id="task-type-select-label">Task type</InputLabel>
              <Select
                labelId="task-type-select-label"
                label="Task type"
                id="task-type-select"
                value={searchParams.get('task_type') || ''}
                onChange={(event) => {
                  updateFilterValue(event.target.value, 'task_type');
                }}
              >
                {taskTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item md={4}>
            <FormControl fullWidth>
              <InputLabel id="event-type-select-label">Event type</InputLabel>
              <Select
                labelId="event-type-select-label"
                label="Event type"
                id="event-type-select"
                value={searchParams.get('event_type') || ''}
                onChange={(event) => {
                  updateFilterValue(event.target.value, 'event_type');
                }}
              >
                {eventTypes.map((type) => (
                  <MenuItem key={type} value={type}>
                    {type}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
        </>,
      );
    }

    return (
      <>
        <Grid container spacing={2} className="with-bottom-margin">
          {filterElements}
        </Grid>
        <Grid container spacing={2} className="with-bottom-margin">
          <Grid item sm={4} md={4} lg={8}>
            <Button variant="outlined" onClick={resetFiltersAndRun}>
              Reset
            </Button>
            {shouldDisplayClearButton && (
              <Button variant="outlined" onClick={clearFilters}>
                Clear
              </Button>
            )}
          </Grid>
        </Grid>
      </>
    );
  };

  const { page, perPage } = getPageInfoFromSearchParams(
    searchParams,
    undefined,
    undefined,
    paginationQueryParamPrefix,
  );
  if (clearAll) {
    return <p>Page cleared 👍</p>;
  }

  return (
    <>
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
        paginationQueryParamPrefix={paginationQueryParamPrefix}
        paginationDataQATag={`pagination-options-${tableType}`}
      />
    </>
  );
}

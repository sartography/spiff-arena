import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ErrorOutline } from '@mui/icons-material';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Modal,
  CircularProgress,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Box,
} from '@mui/material';
import Grid from '@mui/material/Grid';
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
  modifiedProcessModelId: string;
  processInstanceId: number;
};

const style = {
  position: 'absolute' as 'absolute',
  top: '50%',
  left: '50%',
  transform: 'translate(-50%, -50%)',
  width: '80%', // Increased width
  maxWidth: 'md', // Added max width for responsiveness
  maxHeight: '90vh', // Limit height to 90% of viewport height
  bgcolor: 'background.paper',
  border: '2px solid #000',
  boxShadow: 24,
  p: 4,
  overflow: 'auto', // Enable scrolling for large content
};

export default function ProcessInstanceLogList({
  variant,
  isEventsView = true,
  modifiedProcessModelId,
  processInstanceId,
}: OwnProps) {
  const [clearAll, setClearAll] = useState<boolean>(false);
  const { t } = useTranslation();
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

  let processInstanceShowPageBaseUrl = `/process-instances/for-me/${modifiedProcessModelId}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = `/process-instances/${modifiedProcessModelId}`;
  }
  const taskNameHeader = isEventsView ? t('task_name') : t('milestone');
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
      path: `/v1.0/logs/typeahead-filter-values/${modifiedProcessModelId}/${processInstanceId}${typeaheadQueryParamString}`,
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
    modifiedProcessModelId,
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
      const modalHeading = t('event_error_details');
      let errorMessageTag = (
        <CircularProgress className="some-class" size={20} />
      );
      if (eventErrorDetails) {
        const errorForDisplay = errorForDisplayFromProcessInstanceErrorDetail(
          eventForModal,
          eventErrorDetails,
        );
        const errorChildren = childrenForErrorObject(errorForDisplay, t);
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
            <p id="modal-description">{t('error_details')}</p>
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
            message: `${t('error_retrieving_error_details')}: ${error.message}`,
            stacktrace: [],
          };
          setEventErrorDetails(errorObject);
        },
      });
    } else {
      const notAuthorized: ProcessInstanceEventErrorDetail = {
        id: 0,
        message: t('not_authorized_to_view_error_details'),
        stacktrace: [],
      };
      setEventErrorDetails(notAuthorized);
    }
  };

  const eventTypeCell = (logEntry: ProcessInstanceLogEntry) => {
    if (
      ['process_instance_error', 'task_failed'].includes(logEntry.event_type)
    ) {
      const errorTitle = t('event_has_error');
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
        taskName = t('started');
      } else if (logEntry.bpmn_task_type === 'EndEvent') {
        taskName = t('completed');
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
          <TableCell data-testid="paginated-entity-id">{logEntry.id}</TableCell>
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
            data-testid="process-instance-show-link"
            to={`${processInstanceShowPageBaseUrl}/${logEntry.process_instance_id}/${logEntry.spiff_task_guid}`}
            title={t('view_state_when_task_was_completed')}
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
          <TableCell>{t('id')}</TableCell>
          <TableCell>{t('bpmn_process')}</TableCell>
          <TableCell>{taskNameHeader}</TableCell>
          <TableCell>{t('task_identifier')}</TableCell>
          <TableCell>{t('task_type')}</TableCell>
          <TableCell>{t('event_type')}</TableCell>
          <TableCell>{t('user')}</TableCell>
        </>,
      );
    } else {
      tableHeaders.push(
        <>
          <TableCell>{taskNameHeader}</TableCell>
          <TableCell>{t('bpmn_process')}</TableCell>
        </>,
      );
    }
    tableHeaders.push(<TableCell>{t('timestamp')}</TableCell>);
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
      <Grid size={{ md: 4 }}>
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
          <Grid size={{ md: 4 }}>
            <FormControl fullWidth>
              <InputLabel id="task-identifier-filter-label">
                {t('task_identifier')}
              </InputLabel>
              <Select
                labelId="task-identifier-filter-label"
                label={t('task_identifier')}
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
          <Grid size={{ md: 4 }}>
            <FormControl fullWidth>
              <InputLabel id="task-type-select-label">
                {t('task_type')}
              </InputLabel>
              <Select
                labelId="task-type-select-label"
                label={t('task_type')}
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
          <Grid size={{ md: 4 }}>
            <FormControl fullWidth>
              <InputLabel id="event-type-select-label">
                {t('event_type')}
              </InputLabel>
              <Select
                labelId="event-type-select-label"
                label={t('event_type')}
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
          <Grid size={{ sm: 4, md: 4, lg: 8 }}>
            <Button variant="outlined" onClick={resetFiltersAndRun}>
              {t('reset')}
            </Button>
            {shouldDisplayClearButton && (
              <Button variant="outlined" onClick={clearFilters}>
                {t('clear')}
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
    return <p>{t('page_cleared')} 👍</p>;
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
        paginationDataTestidTag={`pagination-options-${tableType}`}
      />
    </>
  );
}

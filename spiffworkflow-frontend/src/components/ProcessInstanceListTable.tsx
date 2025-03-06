import { ArrowRightAlt, OpenInNew, Refresh } from '@mui/icons-material';
import {
  TableRow,
  Table,
  TableHead,
  Button,
  TableCell,
  TableBody,
  TableContainer,
  TableSortLabel,
  Typography,
  IconButton,
} from '@mui/material';
import Grid from '@mui/material/Grid2';
import { useCallback, useEffect, useRef, useState } from 'react';
import 'react-datepicker/dist/react-datepicker.css';
import { useNavigate, useSearchParams } from 'react-router-dom';

import {
  getLastMilestoneFromProcessInstance,
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  refreshAtInterval,
  titleizeString,
} from '../helpers';

import {
  PaginationObject,
  ProcessInstance,
  ProcessInstanceReport,
  ReportColumn,
  ReportFilter,
  ReportMetadata,
  SpiffTableHeader,
} from '../interfaces';
import DateAndTimeService from '../services/DateAndTimeService';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';
import PaginationForTable from './PaginationForTable';
import TableCellWithTimeAgoInWords from './TableCellWithTimeAgoInWords';
import {
  childrenForErrorObject,
  errorForDisplayFromString,
} from './ErrorDisplay';
import SpiffTooltip from './SpiffTooltip';

type OwnProps = {
  additionalReportFilters?: ReportFilter[];
  autoReload?: boolean;
  canCompleteAllTasks?: boolean;
  filterComponent?: Function;
  header?: SpiffTableHeader;
  onProcessInstanceTableListUpdate?: Function;
  paginationClassName?: string;
  paginationQueryParamPrefix?: string;
  perPageOptions?: number[];
  reportIdentifier?: string;
  reportMetadata?: ReportMetadata;
  showActionsColumn?: boolean;
  showLinkToReport?: boolean;
  showRefreshButton?: boolean;
  tableHtmlId?: string;
  textToShowIfEmpty?: string;
  variant?: string;
};

export default function ProcessInstanceListTable({
  additionalReportFilters,
  autoReload = false,
  canCompleteAllTasks = false,
  filterComponent,
  header,
  onProcessInstanceTableListUpdate,
  paginationClassName,
  paginationQueryParamPrefix,
  perPageOptions,
  reportIdentifier,
  reportMetadata,
  showActionsColumn = false,
  showLinkToReport = false,
  showRefreshButton = false,
  tableHtmlId,
  textToShowIfEmpty,
  variant = 'for-me',
}: OwnProps) {
  const navigate = useNavigate();
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [searchParams] = useSearchParams();

  const [processInstances, setProcessInstances] = useState<ProcessInstance[]>(
    [],
  );
  const [
    reportMetadataFromProcessInstances,
    setReportMetadataFromProcessInstances,
  ] = useState<ReportMetadata | null>(null);

  const [reportHash, setReportHash] = useState<string | null>(null);
  const preferredUsername = UserService.getPreferredUsername();
  const userEmail = UserService.getUserEmail();
  const processInstanceShowPathPrefix =
    variant === 'all' ? '/process-instances' : '/process-instances/for-me';

  let processInstanceApiSearchPath = '/process-instances/for-me';
  if (variant === 'all') {
    processInstanceApiSearchPath = '/process-instances';
  }

  const clearRefreshRef = useRef<any>(null);
  const stopRefreshing = useCallback((error: any) => {
    if (clearRefreshRef.current) {
      clearRefreshRef.current();
    }
    if (error) {
      console.error(error);
    }
  }, []);

  const setProcessInstancesFromResult = useCallback(
    (result: any) => {
      const processInstancesFromApi = result.results;
      setProcessInstances(processInstancesFromApi);
      setPagination(result.pagination);
      setReportMetadataFromProcessInstances(result.report_metadata);
      setReportHash(result.report_hash);
      if (onProcessInstanceTableListUpdate) {
        onProcessInstanceTableListUpdate(result);
      }
    },
    [onProcessInstanceTableListUpdate],
  );

  const getProcessInstances = useCallback(
    (reportMetadataArg: ReportMetadata | undefined | null = reportMetadata) => {
      let reportMetadataToUse: ReportMetadata = {
        columns: [],
        filter_by: [],
        order_by: [],
      };
      if (reportMetadataArg) {
        reportMetadataToUse = reportMetadataArg;
      }

      const { page, perPage } = getPageInfoFromSearchParams(
        searchParams,
        undefined,
        undefined,
        paginationQueryParamPrefix,
      );
      let perPageToUse = perPage;
      if (perPageOptions && !perPageOptions.includes(perPageToUse)) {
        // eslint-disable-next-line prefer-destructuring
        perPageToUse = perPageOptions[1];
      }
      if (additionalReportFilters) {
        additionalReportFilters.forEach((arf: ReportFilter) => {
          if (!reportMetadataToUse.filter_by.includes(arf)) {
            reportMetadataToUse.filter_by.push(arf);
          }
        });
      }

      const queryParamString = `per_page=${perPageToUse}&page=${page}`;
      HttpService.makeCallToBackend({
        path: `${processInstanceApiSearchPath}?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
        httpMethod: 'POST',
        failureCallback: stopRefreshing,
        onUnauthorized: stopRefreshing,
        postBody: {
          report_metadata: reportMetadataToUse,
        },
      });
    },
    [
      additionalReportFilters,
      paginationQueryParamPrefix,
      perPageOptions,
      processInstanceApiSearchPath,
      reportMetadata,
      searchParams,
      setProcessInstancesFromResult,
      stopRefreshing,
    ],
  );

  useEffect(() => {
    const setReportMetadataFromReport = (
      processInstanceReport: ProcessInstanceReport,
    ) => {
      getProcessInstances(processInstanceReport.report_metadata);
    };
    const checkForReportAndRun = () => {
      if (reportIdentifier) {
        const queryParamString = `?report_identifier=${reportIdentifier}`;
        HttpService.makeCallToBackend({
          path: `/process-instances/report-metadata${queryParamString}`,
          successCallback: setReportMetadataFromReport,
          onUnauthorized: () => stopRefreshing,
        });
      } else {
        getProcessInstances();
      }
    };
    checkForReportAndRun();

    if (autoReload) {
      clearRefreshRef.current = refreshAtInterval(
        DateAndTimeService.REFRESH_INTERVAL_SECONDS,
        DateAndTimeService.REFRESH_TIMEOUT_SECONDS,
        checkForReportAndRun,
      );
      return clearRefreshRef.current;
    }
    return undefined;
  }, [
    autoReload,
    getProcessInstances,
    reportIdentifier,
    reportMetadata,
    stopRefreshing,
  ]);

  const reportColumns = () => {
    if (reportMetadataFromProcessInstances) {
      return reportMetadataFromProcessInstances.columns;
    }
    return [];
  };

  const getProcessModelSpanTag = (
    _processInstance: ProcessInstance,
    identifier: string,
  ) => {
    return <span>{identifier}</span>;
  };
  const navigateToProcessInstance = (processInstance: ProcessInstance) => {
    navigate(
      `${processInstanceShowPathPrefix}/${modifyProcessIdentifierForPathParam(
        processInstance.process_model_identifier,
      )}/${processInstance.id}`,
    );
  };

  const getWaitingForTableCellComponent = (processInstanceTask: any) => {
    let fullUsernameString = '';
    let shortUsernameString = '';
    if (processInstanceTask.potential_owner_usernames) {
      fullUsernameString = processInstanceTask.potential_owner_usernames;
      const usernames =
        processInstanceTask.potential_owner_usernames.split(',');
      const firstTwoUsernames = usernames.slice(0, 2);
      if (usernames.length > 2) {
        firstTwoUsernames.push('...');
      }
      shortUsernameString = firstTwoUsernames.join(',');
    }
    if (processInstanceTask.assigned_user_group_identifier) {
      fullUsernameString = processInstanceTask.assigned_user_group_identifier;
      shortUsernameString = processInstanceTask.assigned_user_group_identifier;
    }
    return <span title={fullUsernameString}>{shortUsernameString}</span>;
  };
  const formatProcessInstanceId = (
    processInstance: ProcessInstance,
    id: number,
  ) => {
    return <span data-qa="paginated-entity-id">{id}</span>;
  };
  const formatProcessModelIdentifier = (
    processInstance: ProcessInstance,
    identifier: any,
  ) => {
    return getProcessModelSpanTag(processInstance, identifier);
  };
  const formatProcessModelDisplayName = (
    processInstance: ProcessInstance,
    identifier: any,
  ) => {
    return getProcessModelSpanTag(processInstance, identifier);
  };
  const formatLastMilestone = (
    processInstance: ProcessInstance,
    value: any,
  ) => {
    const [valueToUse, truncatedValue] = getLastMilestoneFromProcessInstance(
      processInstance,
      value,
    );
    return <span title={valueToUse}>{truncatedValue}</span>;
  };

  const formatProcessInstanceStatus = (_row: any, value: any) => {
    return titleizeString((value || '').replaceAll('_', ' '));
  };

  const formatDurationForDisplayForTable = (_row: any, value: any) => {
    return DateAndTimeService.formatDurationForDisplay(value);
  };
  const formatDateTimeForTable = (_row: any, value: any) => {
    return DateAndTimeService.formatDateTime(value);
  };

  const formatSecondsForDisplay = (_row: ProcessInstance, seconds: any) => {
    return DateAndTimeService.convertSecondsToFormattedDateTime(seconds) || '-';
  };
  const defaultFormatter = (_row: ProcessInstance, value: any) => {
    return value;
  };
  const formattedColumn = (
    processInstance: ProcessInstance,
    column: ReportColumn,
  ) => {
    const reportColumnFormatters: Record<string, any> = {
      id: formatProcessInstanceId,
      process_model_identifier: formatProcessModelIdentifier,
      process_model_display_name: formatProcessModelDisplayName,
      status: formatProcessInstanceStatus,
      start_in_seconds: formatSecondsForDisplay,
      end_in_seconds: formatSecondsForDisplay,
      updated_at_in_seconds: formatSecondsForDisplay,
      task_updated_at_in_seconds: formatSecondsForDisplay,
      last_milestone_bpmn_name: formatLastMilestone,
    };
    const displayTypeFormatters: Record<string, any> = {
      date_time: formatDateTimeForTable,
      duration: formatDurationForDisplayForTable,
    };
    const columnAccessor = column.accessor as keyof ProcessInstance;
    const formatter = column.display_type
      ? displayTypeFormatters[column.display_type]
      : reportColumnFormatters[columnAccessor] ?? defaultFormatter;
    const value = processInstance[columnAccessor];

    if (columnAccessor === 'status') {
      return (
        <TableCell
          onClick={() => navigateToProcessInstance(processInstance)}
          onKeyDown={() => navigateToProcessInstance(processInstance)}
          data-qa={`process-instance-status-${value}`}
        >
          {formatter(processInstance, value)}
        </TableCell>
      );
    }
    if (columnAccessor === 'updated_at_in_seconds') {
      return (
        <TableCellWithTimeAgoInWords
          timeInSeconds={processInstance.updated_at_in_seconds}
          onClick={() => navigateToProcessInstance(processInstance)}
          onKeyDown={() => navigateToProcessInstance(processInstance)}
        />
      );
    }
    if (columnAccessor === 'task_updated_at_in_seconds') {
      return (
        <TableCellWithTimeAgoInWords
          timeInSeconds={processInstance.task_updated_at_in_seconds || 0}
          onClick={() => navigateToProcessInstance(processInstance)}
          onKeyDown={() => navigateToProcessInstance(processInstance)}
        />
      );
    }
    let cellContent: any = null;
    if (columnAccessor === 'process_model_display_name') {
      cellContent = formatter(processInstance, value);
    } else if (columnAccessor === 'waiting_for') {
      cellContent = getWaitingForTableCellComponent(processInstance);
    } else {
      cellContent = formatter(processInstance, value);
    }
    return (
      <TableCell
        key={`td-${columnAccessor}-${processInstance.id}`}
        onClick={() => navigateToProcessInstance(processInstance)}
        onKeyDown={() => navigateToProcessInstance(processInstance)}
        data-qa={`process-instance-show-link-${columnAccessor}`}
      >
        {cellContent}
      </TableCell>
    );
  };

  const tableTitle = () => {
    let headerTextElement = null;
    if (header) {
      headerTextElement = header.text;
      if (header.text.includes('**')) {
        const parts = header.text.split('**');
        if (parts.length === 3) {
          headerTextElement = (
            <>
              {parts[0]}
              <strong>{parts[1]}</strong>
              {parts[2]}
            </>
          );
        }
      }
    }

    if (header) {
      return (
        <Grid container alignItems="center" spacing={1}>
          <Grid>
            <Typography variant="h3" title={header.tooltip_text}>
              {headerTextElement}
            </Typography>
          </Grid>
          {showRefreshButton ? (
            <Grid>
              <SpiffTooltip title="Refresh data in the table">
                <IconButton
                  data-qa="refresh-process-instance-table"
                  onClick={() => getProcessInstances()}
                >
                  <Refresh />
                </IconButton>
              </SpiffTooltip>
            </Grid>
          ) : null}
        </Grid>
      );
    }
    return null;
  };

  const tableTitleLine = () => {
    if (!showLinkToReport && !header) {
      return null;
    }

    let filterButtonLink = null;
    if (showLinkToReport && pagination && pagination.total) {
      filterButtonLink = (
        <Grid style={{ textAlign: 'right' }} offset="auto">
          <SpiffTooltip title="View Filterable List" placement="top">
            <IconButton
              data-qa="process-instance-list-link"
              onClick={() =>
                navigate(`/process-instances?report_hash=${reportHash}`)
              }
            >
              <ArrowRightAlt />
            </IconButton>
          </SpiffTooltip>
        </Grid>
      );
    }
    if (!header && !filterButtonLink) {
      return null;
    }
    return (
      <Grid container alignItems="center" spacing={1}>
        <Grid>{tableTitle()}</Grid>
        {filterButtonLink}
      </Grid>
    );
  };

  const buildTable = () => {
    const headers = reportColumns().map((column: ReportColumn) => {
      return column.Header;
    });
    if (showActionsColumn) {
      headers.push('Action');
    }

    const rows = processInstances.map((processInstance: ProcessInstance) => {
      const currentRow = reportColumns().map((column: ReportColumn) => {
        return formattedColumn(processInstance, column);
      });
      if (showActionsColumn) {
        let goButtonElement = null;
        const taskShowUrl = `/tasks/${processInstance.id}/${processInstance.task_id}`;
        const regex = new RegExp(`\\b(${preferredUsername}|${userEmail})\\b`);
        let hasAccessToCompleteTask = false;
        if (
          canCompleteAllTasks ||
          (processInstance.potential_owner_usernames || '').match(regex)
        ) {
          hasAccessToCompleteTask = true;
        }
        if (hasAccessToCompleteTask && processInstance.task_id) {
          goButtonElement = (
            <Button
              variant="contained"
              href={taskShowUrl}
              style={{ width: '60px' }}
              size="small"
            >
              Go
            </Button>
          );
        }
        const piLink = `${processInstanceShowPathPrefix}/${modifyProcessIdentifierForPathParam(
          processInstance.process_model_identifier,
        )}/${processInstance.id}`;
        const piShowButtonElement = (
          <IconButton
            href={piLink}
            target="_blank"
            style={{ width: '50px' }}
            size="small"
          >
            <OpenInNew />
          </IconButton>
        );

        const statusesToExcludeTaskButton = [
          'error',
          'terminated',
          'suspended',
        ];
        if (!(processInstance.status in statusesToExcludeTaskButton)) {
          currentRow.push(
            <TableCell align="right">
              {goButtonElement}
              {piShowButtonElement}
            </TableCell>,
          );
        } else {
          currentRow.push(<TableCell>{piShowButtonElement}</TableCell>);
        }
      }

      const rowStyle = { cursor: 'pointer' };
      let variantFromMetadata = 'all';
      if (reportMetadataFromProcessInstances) {
        reportMetadataFromProcessInstances.filter_by.forEach((filter: any) => {
          if (
            filter.field_name === 'with_relation_to_me' &&
            filter.field_value
          ) {
            variantFromMetadata = 'for-me';
          }
        });
      }

      return (
        <TableRow
          style={rowStyle}
          key={processInstance.id}
          className={`process-instance-list-row-variant-${variantFromMetadata}`}
        >
          {currentRow}
        </TableRow>
      );
    });

    let tableProps: any = { size: 'lg' };
    if (tableHtmlId) {
      tableProps = { ...tableProps, id: tableHtmlId };
    }

    return (
      <TableContainer>
        {/* eslint-disable-next-line react/jsx-props-no-spreading */}
        <Table size="medium" {...tableProps} className="process-instance-list">
          <TableHead>
            <TableRow>
              {headers.map((tableRowHeader: any) => (
                <TableCell
                  key={tableRowHeader}
                  title={
                    tableRowHeader === 'Id' ? 'Process Instance Id' : undefined
                  }
                >
                  <TableSortLabel>{tableRowHeader}</TableSortLabel>
                </TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>{rows}</TableBody>
        </Table>
      </TableContainer>
    );
  };

  const errors: string[] = [];
  if (additionalReportFilters && reportMetadata) {
    errors.push(
      'Both reportMetadata and additionalReportFilters were provided. ' +
        'It is recommended to only use additionalReportFilters with reportIdentifier and to specify ALL filters in reportMetadata if not using reportIdentifier.',
    );
  }
  if (reportIdentifier && reportMetadata) {
    errors.push(
      'Both reportIdentifier and reportMetadata were provided. ' +
        'You must use one or the other.',
    );
  }
  if (errors.length > 0) {
    return (
      <Grid container>
        {tableTitleLine()}
        <Grid size={{ xs: 12 }}>
          {childrenForErrorObject(
            errorForDisplayFromString(errors.join(' ::: ')),
          )}
        </Grid>
      </Grid>
    );
  }

  let tableElement = null;
  if (pagination && (!textToShowIfEmpty || pagination.total > 0)) {
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix,
    );
    let perPageToUse = perPage;
    if (perPageOptions && !perPageOptions.includes(perPageToUse)) {
      // eslint-disable-next-line prefer-destructuring
      perPageToUse = perPageOptions[1];
    }
    tableElement = (
      <PaginationForTable
        page={page}
        perPage={perPageToUse}
        pagination={pagination}
        tableToDisplay={buildTable()}
        paginationQueryParamPrefix={paginationQueryParamPrefix}
        perPageOptions={perPageOptions}
        paginationClassName={paginationClassName}
      />
    );
  } else if (textToShowIfEmpty) {
    tableElement = (
      <Typography
        variant="body1"
        className="no-results-message with-large-bottom-margin"
      >
        {textToShowIfEmpty}
      </Typography>
    );
  }
  return (
    <>
      {tableTitleLine()}
      <br />
      {filterComponent ? filterComponent() : null}
      <Grid container>
        <Grid size={{ xs: 12 }}>{tableElement}</Grid>
      </Grid>
    </>
  );
}

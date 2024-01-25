import { ArrowRight } from '@carbon/icons-react';
import {
  Grid,
  Column,
  TableRow,
  Table,
  TableHeader,
  TableHead,
  Button,
} from '@carbon/react';
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

type OwnProps = {
  additionalReportFilters?: ReportFilter[];
  autoReload?: boolean;
  canCompleteAllTasks?: boolean;
  header?: SpiffTableHeader;
  onProcessInstanceTableListUpdate?: Function;
  paginationClassName?: string;
  paginationQueryParamPrefix?: string;
  perPageOptions?: number[];
  reportIdentifier?: string;
  reportMetadata?: ReportMetadata;
  showActionsColumn?: boolean;
  showLinkToReport?: boolean;
  tableHtmlId?: string;
  textToShowIfEmpty?: string;
  variant?: string;
};

export default function ProcessInstanceListTable({
  additionalReportFilters,
  autoReload = false,
  canCompleteAllTasks = false,
  header,
  onProcessInstanceTableListUpdate,
  paginationClassName,
  paginationQueryParamPrefix,
  perPageOptions,
  reportIdentifier,
  reportMetadata,
  showActionsColumn = false,
  showLinkToReport = false,
  tableHtmlId,
  textToShowIfEmpty,
  variant = 'for-me',
}: OwnProps) {
  const navigate = useNavigate();
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [searchParams] = useSearchParams();

  const [processInstances, setProcessInstances] = useState<ProcessInstance[]>(
    []
  );
  const [
    reportMetadataFromProcessInstances,
    setreportMetadataFromProcessInstances,
  ] = useState<ReportMetadata | null>(null);
  const [rmHash, setRmHash] = useState<string>('');

  // this is used from pages like the home page that have multiple tables
  // and cannot store the report hash in the query params.
  // it can be used to create a link to the process instances list page to reconstruct the report.
  const [reportHash, setReportHash] = useState<string | null>(null);
  const preferredUsername = UserService.getPreferredUsername();
  const userEmail = UserService.getUserEmail();
  const processInstanceShowPathPrefix =
    variant === 'all' ? '/process-instances' : '/process-instances/for-me';

  // eslint-disable-next-line sonarjs/no-duplicate-string
  let processInstanceApiSearchPath = '/process-instances/for-me';
  if (variant === 'all') {
    processInstanceApiSearchPath = '/process-instances';
  }

  // Useful to stop refreshing if an api call gets an error
  // since those errors can make the page unusable in any way
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
      setreportMetadataFromProcessInstances(result.report_metadata);
      setReportHash(result.report_hash);
      if (onProcessInstanceTableListUpdate) {
        onProcessInstanceTableListUpdate(result);
      }
    },
    [onProcessInstanceTableListUpdate]
  );

  const getProcessInstances = useCallback(
    (reportMetadataArg: ReportMetadata | undefined | null = reportMetadata) => {
      // eslint-disable-next-line prefer-const
      let { page, perPage } = getPageInfoFromSearchParams(
        searchParams,
        undefined,
        undefined,
        paginationQueryParamPrefix
      );

      const newRmHash = JSON.stringify(reportMetadata) + page + perPage;
      console.log('newRmHash', newRmHash);
      console.log('rmHash', rmHash);
      if (rmHash && rmHash === newRmHash) {
        return;
      }
      setRmHash(newRmHash);
      let reportMetadataToUse: ReportMetadata = {
        columns: [],
        filter_by: [],
        order_by: [],
      };
      if (reportMetadataArg) {
        reportMetadataToUse = reportMetadataArg;
      }
      if (perPageOptions && !perPageOptions.includes(perPage)) {
        // eslint-disable-next-line prefer-destructuring
        perPage = perPageOptions[1];
      }
      if (additionalReportFilters) {
        additionalReportFilters.forEach((arf: ReportFilter) => {
          if (!reportMetadataToUse.filter_by.includes(arf)) {
            reportMetadataToUse.filter_by.push(arf);
          }
        });
      }

      const queryParamString = `per_page=${perPage}&page=${page}`;
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
      rmHash,
      searchParams,
      setProcessInstancesFromResult,
      stopRefreshing,
    ]
  );

  useEffect(() => {
    console.log('NO HERE');
    const setReportMetadataFromReport = (
      processInstanceReport: ProcessInstanceReport
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
    if (reportIdentifier || reportMetadata) {
      checkForReportAndRun();

      if (autoReload) {
        clearRefreshRef.current = refreshAtInterval(
          DateAndTimeService.REFRESH_INTERVAL_SECONDS,
          DateAndTimeService.REFRESH_TIMEOUT_SECONDS,
          checkForReportAndRun
        );
        return clearRefreshRef.current;
      }
    }
    return undefined;
  }, [
    autoReload,
    getProcessInstances,
    reportIdentifier,
    reportMetadata,
    // reportMetadataInteger,
    setProcessInstancesFromResult,
    stopRefreshing,
  ]);

  const reportColumns = () => {
    if (reportMetadataFromProcessInstances) {
      return reportMetadataFromProcessInstances.columns;
    }
    return [];
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
  const formatProcessInstanceId = (_row: ProcessInstance, id: number) => {
    return <span data-qa="paginated-entity-id">{id}</span>;
  };
  const formatProcessModelIdentifier = (
    _row: ProcessInstance,
    identifier: any
  ) => {
    return <span>{identifier}</span>;
  };
  const formatProcessModelDisplayName = (
    _row: ProcessInstance,
    identifier: any
  ) => {
    return <span>{identifier}</span>;
  };
  const formatLastMilestone = (
    processInstance: ProcessInstance,
    value: any
  ) => {
    const [valueToUse, truncatedValue] = getLastMilestoneFromProcessInstance(
      processInstance,
      value
    );
    return <span title={valueToUse}>{truncatedValue}</span>;
  };

  const formatProcessInstanceStatus = (_row: any, value: any) => {
    return titleizeString((value || '').replaceAll('_', ' '));
  };

  const formatSecondsForDisplay = (_row: ProcessInstance, seconds: any) => {
    return DateAndTimeService.convertSecondsToFormattedDateTime(seconds) || '-';
  };
  const defaultFormatter = (_row: ProcessInstance, value: any) => {
    return value;
  };
  const formattedColumn = (row: ProcessInstance, column: ReportColumn) => {
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
      date_time: DateAndTimeService.formatDateTime,
      duration: DateAndTimeService.formatDurationForDisplay,
    };
    const columnAccessor = column.accessor as keyof ProcessInstance;
    const formatter = column.display_type
      ? displayTypeFormatters[column.display_type]
      : reportColumnFormatters[columnAccessor] ?? defaultFormatter;
    const value = row[columnAccessor];

    if (columnAccessor === 'status') {
      return (
        <td data-qa={`process-instance-status-${value}`}>
          {formatter(row, value)}
        </td>
      );
    }
    if (columnAccessor === 'process_model_display_name') {
      return <td> {formatter(row, value)} </td>;
    }
    if (columnAccessor === 'waiting_for') {
      return <td> {getWaitingForTableCellComponent(row)} </td>;
    }
    if (columnAccessor === 'updated_at_in_seconds') {
      return (
        <TableCellWithTimeAgoInWords
          timeInSeconds={row.updated_at_in_seconds}
        />
      );
    }
    if (columnAccessor === 'task_updated_at_in_seconds') {
      return (
        <TableCellWithTimeAgoInWords
          timeInSeconds={row.task_updated_at_in_seconds || 0}
        />
      );
    }
    return (
      // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
      <td data-qa={`process-instance-show-link-${columnAccessor}`}>
        {formatter(row, value)}
      </td>
    );
  };

  const tableTitleLine = () => {
    if (!showLinkToReport && !header) {
      return null;
    }

    let filterButtonLink = null;
    if (showLinkToReport && pagination && pagination.total) {
      filterButtonLink = (
        <Column
          sm={{ span: 1, offset: 3 }}
          md={{ span: 1, offset: 7 }}
          lg={{ span: 1, offset: 15 }}
          style={{ textAlign: 'right' }}
        >
          <Button
            data-qa="process-instance-list-link"
            renderIcon={ArrowRight}
            iconDescription="View Filterable List"
            hasIconOnly
            size="md"
            onClick={() =>
              navigate(`/process-instances?report_hash=${reportHash}`)
            }
          />
        </Column>
      );
    }
    if (!header && !filterButtonLink) {
      return null;
    }
    let headerTextElement = null;
    if (header) {
      headerTextElement = header.text;
      // poor man's markdown, just so we can allow bolded words in headers
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
    return (
      <>
        <Column
          sm={{ span: 3 }}
          md={{ span: 7 }}
          lg={{ span: 15 }}
          style={{ height: '48px' }}
        >
          {header ? (
            <h2
              title={header.tooltip_text}
              className="process-instance-table-header"
            >
              {headerTextElement}
            </h2>
          ) : null}
        </Column>
        {filterButtonLink}
      </>
    );
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
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
        let buttonElement = null;
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
          buttonElement = (
            <Button
              kind="secondary"
              href={taskShowUrl}
              style={{ width: '60px' }}
              size="sm"
            >
              Go
            </Button>
          );
        }

        const statusesToExcludeTaskButton = [
          'error',
          'terminated',
          'suspended',
        ];
        if (!(processInstance.status in statusesToExcludeTaskButton)) {
          currentRow.push(<td>{buttonElement}</td>);
        } else {
          currentRow.push(<td />);
        }
      }

      const rowStyle = { cursor: 'pointer' };
      const modifiedModelId = modifyProcessIdentifierForPathParam(
        processInstance.process_model_identifier
      );
      const navigateToProcessInstance = () => {
        navigate(
          `${processInstanceShowPathPrefix}/${modifiedModelId}/${processInstance.id}`
        );
      };
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
        // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
        <tr
          style={rowStyle}
          key={processInstance.id}
          onClick={navigateToProcessInstance}
          onKeyDown={navigateToProcessInstance}
          className={`process-instance-list-row-variant-${variantFromMetadata}`}
        >
          {currentRow}
        </tr>
      );
    });

    let tableProps: any = { size: 'lg' };
    if (tableHtmlId) {
      tableProps = { ...tableProps, id: tableHtmlId };
    }

    return (
      // eslint-disable-next-line react/jsx-props-no-spreading
      <Table {...tableProps} className="process-instance-list">
        <TableHead>
          <TableRow>
            {headers.map((tableRowHeader: any) => (
              <TableHeader
                key={tableRowHeader}
                title={tableRowHeader === 'Id' ? 'Process Instance Id' : null}
              >
                {tableRowHeader}
              </TableHeader>
            ))}
          </TableRow>
        </TableHead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const errors: string[] = [];
  if (additionalReportFilters && reportMetadata) {
    errors.push(
      'Both reportMetadata and additionalReportFilters were provided. ' +
        'It is recommended to only use additionalReportFilters with reportIdentifier and to specify ALL filters in reportMetadata if not using reportIdentifier.'
    );
  }
  if (reportIdentifier && reportMetadata) {
    errors.push(
      'Both reportIdentifier and reportMetadata were provided. ' +
        'You must use one or the other.'
    );
  }

  let tableElement = null;
  if (pagination && (!textToShowIfEmpty || pagination.total > 0)) {
    // eslint-disable-next-line prefer-const
    let { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      undefined,
      undefined,
      paginationQueryParamPrefix
    );
    if (perPageOptions && !perPageOptions.includes(perPage)) {
      // eslint-disable-next-line prefer-destructuring
      perPage = perPageOptions[1];
    }
    tableElement = (
      <PaginationForTable
        page={page}
        perPage={perPage}
        pagination={pagination}
        tableToDisplay={buildTable()}
        paginationQueryParamPrefix={paginationQueryParamPrefix}
        perPageOptions={perPageOptions}
        paginationClassName={paginationClassName}
      />
    );
  } else if (textToShowIfEmpty) {
    tableElement = (
      <p className="no-results-message with-large-bottom-margin">
        {textToShowIfEmpty}
      </p>
    );
  }

  if (errors.length > 0) {
    return (
      <Grid fullWidth condensed className="megacondensed">
        {tableTitleLine()}
        <Column sm={{ span: 4 }} md={{ span: 8 }} lg={{ span: 16 }}>
          {childrenForErrorObject(
            errorForDisplayFromString(errors.join(' ::: '))
          )}
        </Column>
      </Grid>
    );
  }
  return (
    <Grid fullWidth condensed className="megacondensed">
      {tableTitleLine()}
      <Column sm={{ span: 4 }} md={{ span: 8 }} lg={{ span: 16 }}>
        {tableElement}
      </Column>
    </Grid>
  );
}

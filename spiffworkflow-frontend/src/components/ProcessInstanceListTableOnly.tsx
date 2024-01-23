import { TableRow, Table, TableHeader, TableHead, Button } from '@carbon/react';
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
  ReportColumn,
  ReportMetadata,
} from '../interfaces';
import DateAndTimeService from '../services/DateAndTimeService';
import HttpService from '../services/HttpService';
import UserService from '../services/UserService';
import PaginationForTable from './PaginationForTable';
import TableCellWithTimeAgoInWords from './TableCellWithTimeAgoInWords';

type OwnProps = {
  paginationQueryParamPrefix?: string;
  perPageOptions?: number[];
  textToShowIfEmpty?: string;
  paginationClassName?: string;
  autoReload?: boolean;
  variant?: string;
  canCompleteAllTasks?: boolean;
  showActionsColumn?: boolean;
  tableHtmlId?: string;
  reportMetadata: ReportMetadata;
};

export default function ProcessInstanceListTableOnly({
  paginationQueryParamPrefix,
  perPageOptions,
  textToShowIfEmpty,
  paginationClassName,
  autoReload = false,
  variant = 'for-me',
  canCompleteAllTasks = false,
  showActionsColumn = false,
  tableHtmlId,
  reportMetadata,
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

  useEffect(() => {
    const setProcessInstancesFromResult = (result: any) => {
      const processInstancesFromApi = result.results;
      setProcessInstances(processInstancesFromApi);
      setPagination(result.pagination);
      setreportMetadataFromProcessInstances(result.report_metadata);
    };

    const getProcessInstances = () => {
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

      const queryParamString = `per_page=${perPage}&page=${page}`;
      HttpService.makeCallToBackend({
        path: `${processInstanceApiSearchPath}?${queryParamString}`,
        successCallback: setProcessInstancesFromResult,
        httpMethod: 'POST',
        failureCallback: stopRefreshing,
        onUnauthorized: stopRefreshing,
        postBody: {
          report_metadata: reportMetadata,
        },
      });
    };
    getProcessInstances();

    if (autoReload) {
      clearRefreshRef.current = refreshAtInterval(
        DateAndTimeService.REFRESH_INTERVAL_SECONDS,
        DateAndTimeService.REFRESH_TIMEOUT_SECONDS,
        getProcessInstances
      );
      return clearRefreshRef.current;
    }
    return undefined;
  }, [
    autoReload,
    paginationQueryParamPrefix,
    perPageOptions,
    processInstanceApiSearchPath,
    reportMetadata,
    searchParams,
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
    return (
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
  }
  if (textToShowIfEmpty) {
    return (
      <p className="no-results-message with-large-bottom-margin">
        {textToShowIfEmpty}
      </p>
    );
  }
  return null;
}

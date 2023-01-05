import { useEffect, useState } from 'react';
// @ts-ignore
import { Button, Table } from '@carbon/react';
import { Link, useSearchParams } from 'react-router-dom';
import UserService from '../services/UserService';
import PaginationForTable from './PaginationForTable';
import {
  convertSecondsToFormattedDateTime,
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  refreshAtInterval,
} from '../helpers';
import HttpService from '../services/HttpService';
import { PaginationObject, ProcessInstanceTask } from '../interfaces';
import TableCellWithTimeAgoInWords from './TableCellWithTimeAgoInWords';

const PER_PAGE_FOR_TASKS_ON_HOME_PAGE = 5;
const REFRESH_INTERVAL = 5;
const REFRESH_TIMEOUT = 600;

type OwnProps = {
  apiPath: string;
  tableTitle: string;
  tableDescription: string;
  additionalParams?: string;
  paginationQueryParamPrefix?: string;
  paginationClassName?: string;
  autoReload?: boolean;
  showStartedBy?: boolean;
  showWaitingOn?: boolean;
  textToShowIfEmpty?: string;
};

export default function TaskListTable({
  apiPath,
  tableTitle,
  tableDescription,
  additionalParams,
  paginationQueryParamPrefix,
  paginationClassName,
  textToShowIfEmpty,
  autoReload = false,
  showStartedBy = true,
  showWaitingOn = true,
}: OwnProps) {
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);

  const preferredUsername = UserService.getPreferredUsername();
  const userEmail = UserService.getUserEmail();

  useEffect(() => {
    const getTasks = () => {
      const { page, perPage } = getPageInfoFromSearchParams(
        searchParams,
        PER_PAGE_FOR_TASKS_ON_HOME_PAGE,
        undefined,
        paginationQueryParamPrefix
      );
      const setTasksFromResult = (result: any) => {
        setTasks(result.results);
        setPagination(result.pagination);
      };
      let params = `?per_page=${perPage}&page=${page}`;
      if (additionalParams) {
        params += `&${additionalParams}`;
      }
      HttpService.makeCallToBackend({
        path: `${apiPath}${params}`,
        successCallback: setTasksFromResult,
      });
    };
    getTasks();
    if (autoReload) {
      return refreshAtInterval(REFRESH_INTERVAL, REFRESH_TIMEOUT, getTasks);
    }
    return undefined;
  }, [
    searchParams,
    additionalParams,
    apiPath,
    paginationQueryParamPrefix,
    autoReload,
  ]);

  const getWaitingForTableCellComponent = (
    processInstanceTask: ProcessInstanceTask
  ) => {
    let fullUsernameString = '';
    let shortUsernameString = '';
    if (processInstanceTask.assigned_user_group_identifier) {
      fullUsernameString = processInstanceTask.assigned_user_group_identifier;
      shortUsernameString = processInstanceTask.assigned_user_group_identifier;
    }
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
    return <span title={fullUsernameString}>{shortUsernameString}</span>;
  };

  const buildTable = () => {
    if (!tasks) {
      return null;
    }
    const rows = tasks.map((row: ProcessInstanceTask) => {
      const taskUrl = `/tasks/${row.process_instance_id}/${row.task_id}`;
      const modifiedProcessModelIdentifier =
        modifyProcessIdentifierForPathParam(row.process_model_identifier);

      const regex = new RegExp(`\\b(${preferredUsername}|${userEmail})\\b`);
      let hasAccessToCompleteTask = false;
      if (row.potential_owner_usernames.match(regex)) {
        hasAccessToCompleteTask = true;
      }
      return (
        <tr key={row.id}>
          <td>
            <Link
              data-qa="process-instance-show-link"
              to={`/admin/process-instances/for-me/${modifiedProcessModelIdentifier}/${row.process_instance_id}`}
              title={`View process instance ${row.process_instance_id}`}
            >
              {row.process_instance_id}
            </Link>
          </td>
          <td>
            <Link
              data-qa="process-model-show-link"
              to={`/admin/process-models/${modifiedProcessModelIdentifier}`}
              title={row.process_model_identifier}
            >
              {row.process_model_display_name}
            </Link>
          </td>
          <td
            title={`task id: ${row.name}, spiffworkflow task guid: ${row.id}`}
          >
            {row.task_title}
          </td>
          {showStartedBy ? <td>{row.process_initiator_username}</td> : ''}
          {showWaitingOn ? <td>{getWaitingForTableCellComponent(row)}</td> : ''}
          <td>
            {convertSecondsToFormattedDateTime(row.created_at_in_seconds) ||
              '-'}
          </td>
          <TableCellWithTimeAgoInWords
            timeInSeconds={row.updated_at_in_seconds}
          />
          <td>
            <Button
              variant="primary"
              href={taskUrl}
              hidden={row.process_instance_status === 'suspended'}
              disabled={!hasAccessToCompleteTask}
            >
              Go
            </Button>
          </td>
        </tr>
      );
    });
    let tableHeaders = ['Id', 'Process', 'Task'];
    if (showStartedBy) {
      tableHeaders.push('Started By');
    }
    if (showWaitingOn) {
      tableHeaders.push('Waiting For');
    }
    tableHeaders = tableHeaders.concat([
      'Date Started',
      'Last Updated',
      'Actions',
    ]);
    return (
      <Table striped bordered>
        <thead>
          <tr>
            {tableHeaders.map((tableHeader: string) => {
              return <th>{tableHeader}</th>;
            })}
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const tasksComponent = () => {
    if (pagination && pagination.total < 1) {
      return (
        <p className="no-results-message with-large-bottom-margin">
          {textToShowIfEmpty}
        </p>
      );
    }
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      PER_PAGE_FOR_TASKS_ON_HOME_PAGE,
      undefined,
      paginationQueryParamPrefix
    );
    return (
      <PaginationForTable
        page={page}
        perPage={perPage}
        perPageOptions={[2, PER_PAGE_FOR_TASKS_ON_HOME_PAGE, 25]}
        pagination={pagination}
        tableToDisplay={buildTable()}
        paginationQueryParamPrefix={paginationQueryParamPrefix}
        paginationClassName={paginationClassName}
      />
    );
  };

  if (tasks) {
    return (
      <>
        <h2>{tableTitle}</h2>
        <p className="data-table-description">{tableDescription}</p>
        {tasksComponent()}
      </>
    );
  }
  return null;
}

import { useEffect, useState } from 'react';
// @ts-ignore
import { Button, Table } from '@carbon/react';
import { Link, useSearchParams } from 'react-router-dom';
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
};

export default function TasksTable({
  apiPath,
  tableTitle,
  tableDescription,
  additionalParams,
  paginationQueryParamPrefix,
  paginationClassName,
  autoReload = false,
  showStartedBy = true,
  showWaitingOn = true,
}: OwnProps) {
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);

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
      refreshAtInterval(REFRESH_INTERVAL, REFRESH_TIMEOUT, getTasks);
    }
  }, [
    searchParams,
    additionalParams,
    apiPath,
    paginationQueryParamPrefix,
    autoReload,
  ]);

  const buildTable = () => {
    if (!tasks) {
      return null;
    }
    const rows = tasks.map((row) => {
      const rowToUse = row as any;
      const taskUrl = `/tasks/${rowToUse.process_instance_id}/${rowToUse.task_id}`;
      const modifiedProcessModelIdentifier =
        modifyProcessIdentifierForPathParam(rowToUse.process_model_identifier);
      return (
        <tr key={rowToUse.id}>
          <td>
            <Link
              data-qa="process-instance-show-link"
              to={`/admin/process-instances/${modifiedProcessModelIdentifier}/${rowToUse.process_instance_id}`}
              title={`View process instance ${rowToUse.process_instance_id}`}
            >
              {rowToUse.process_instance_id}
            </Link>
          </td>
          <td>
            <Link
              data-qa="process-model-show-link"
              to={`/admin/process-models/${modifiedProcessModelIdentifier}`}
              title={rowToUse.process_model_identifier}
            >
              {rowToUse.process_model_display_name}
            </Link>
          </td>
          <td
            title={`task id: ${rowToUse.name}, spiffworkflow task guid: ${rowToUse.id}`}
          >
            {rowToUse.task_title}
          </td>
          {showStartedBy ? <td>{rowToUse.username}</td> : ''}
          {showWaitingOn ? <td>{rowToUse.group_identifier || '-'}</td> : ''}
          <td>
            {convertSecondsToFormattedDateTime(
              rowToUse.created_at_in_seconds
            ) || '-'}
          </td>
          <TableCellWithTimeAgoInWords
            timeInSeconds={rowToUse.updated_at_in_seconds}
          />
          <td>
            <Button
              variant="primary"
              href={taskUrl}
              hidden={rowToUse.process_instance_status === 'suspended'}
              disabled={!rowToUse.current_user_is_potential_owner}
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
          Your groups have no task assignments at this time.
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

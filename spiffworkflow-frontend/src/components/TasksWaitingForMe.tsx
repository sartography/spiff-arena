import { useEffect, useState } from 'react';
// @ts-ignore
import { Button, Table } from '@carbon/react';
import { Link, useSearchParams } from 'react-router-dom';
import PaginationForTable from './PaginationForTable';
import {
  convertSecondsToFormattedDateTime,
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
} from '../helpers';
import HttpService from '../services/HttpService';
import { PaginationObject } from '../interfaces';

const PER_PAGE_FOR_TASKS_ON_HOME_PAGE = 5;

export default function TasksWaitingForMe() {
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);

  useEffect(() => {
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      PER_PAGE_FOR_TASKS_ON_HOME_PAGE,
      undefined,
      'tasks_waiting_for_me'
    );
    const setTasksFromResult = (result: any) => {
      setTasks(result.results);
      setPagination(result.pagination);
    };
    HttpService.makeCallToBackend({
      path: `/tasks/for-me?per_page=${perPage}&page=${page}`,
      successCallback: setTasksFromResult,
    });
  }, [searchParams]);

  const buildTable = () => {
    const rows = tasks.map((row) => {
      const rowToUse = row as any;
      const taskUrl = `/tasks/${rowToUse.process_instance_id}/${rowToUse.task_id}`;
      const modifiedProcessModelIdentifier =
        modifyProcessIdentifierForPathParam(rowToUse.process_model_identifier);
      return (
        <tr key={rowToUse.id}>
          <td>
            <Link
              data-qa="process-model-show-link"
              to={`/admin/process-models/${modifiedProcessModelIdentifier}`}
            >
              {rowToUse.process_model_display_name}
            </Link>
          </td>
          <td>
            <Link
              data-qa="process-instance-show-link"
              to={`/admin/process-models/${modifiedProcessModelIdentifier}/process-instances/${rowToUse.process_instance_id}`}
            >
              View {rowToUse.process_instance_id}
            </Link>
          </td>
          <td
            title={`task id: ${rowToUse.name}, spiffworkflow task guid: ${rowToUse.id}`}
          >
            {rowToUse.task_title}
          </td>
          <td>{rowToUse.username}</td>
          <td>{rowToUse.process_instance_status}</td>
          <td>{rowToUse.group_identifier || '-'}</td>
          <td>
            {convertSecondsToFormattedDateTime(
              rowToUse.created_at_in_seconds
            ) || '-'}
          </td>
          <td>
            {convertSecondsToFormattedDateTime(
              rowToUse.updated_at_in_seconds
            ) || '-'}
          </td>
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
    return (
      <Table striped bordered>
        <thead>
          <tr>
            <th>Process Model</th>
            <th>Process Instance</th>
            <th>Task Name</th>
            <th>Process Started By</th>
            <th>Process Instance Status</th>
            <th>Assigned Group</th>
            <th>Process Started</th>
            <th>Process Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </Table>
    );
  };

  const tasksComponent = () => {
    if (pagination && pagination.total < 1) {
      return <p>No tasks waiting for you</p>;
    }
    const { page, perPage } = getPageInfoFromSearchParams(
      searchParams,
      PER_PAGE_FOR_TASKS_ON_HOME_PAGE,
      undefined,
      'tasks_waiting_for_me'
    );
    return (
      <PaginationForTable
        page={page}
        perPage={perPage}
        perPageOptions={[2, PER_PAGE_FOR_TASKS_ON_HOME_PAGE, 25]}
        pagination={pagination}
        tableToDisplay={buildTable()}
        paginationQueryParamPrefix="tasks_waiting_for_me"
      />
    );
  };

  return (
    <>
      <h1>Tasks waiting for me</h1>
      {tasksComponent()}
    </>
  );
}

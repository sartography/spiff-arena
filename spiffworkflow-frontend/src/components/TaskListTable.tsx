import { ReactElement, useEffect, useState } from 'react';
import { Button, Table, Modal, Stack } from '@carbon/react';
import { Link, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { TimeAgo } from '../helpers/timeago';
import UserService from '../services/UserService';
import PaginationForTable from './PaginationForTable';
import {
  convertSecondsToFormattedDateTime,
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  refreshAtInterval,
  REFRESH_INTERVAL_SECONDS,
  REFRESH_TIMEOUT_SECONDS,
} from '../helpers';
import HttpService from '../services/HttpService';
import { PaginationObject, ProcessInstanceTask, Task } from '../interfaces';
import TableCellWithTimeAgoInWords from './TableCellWithTimeAgoInWords';
import CustomForm from './CustomForm';

const PER_PAGE_FOR_TASKS_ON_HOME_PAGE = 5;

type OwnProps = {
  apiPath: string;
  tableTitle?: string;
  tableDescription?: string;
  additionalParams?: string;
  paginationQueryParamPrefix?: string;
  paginationClassName?: string;
  autoReload?: boolean;
  showStartedBy?: boolean;
  showWaitingOn?: boolean;
  textToShowIfEmpty?: string;
  shouldPaginateTable?: boolean;
  showProcessId?: boolean;
  showProcessModelIdentifier?: boolean;
  showTableDescriptionAsTooltip?: boolean;
  showDateStarted?: boolean;
  showLastUpdated?: boolean;
  hideIfNoTasks?: boolean;
  canCompleteAllTasks?: boolean;
  showActionsColumn?: boolean;
  showViewFormDataButton?: boolean;
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
  shouldPaginateTable = true,
  showProcessId = true,
  showProcessModelIdentifier = true,
  showTableDescriptionAsTooltip = false,
  showDateStarted = true,
  showLastUpdated = true,
  hideIfNoTasks = false,
  canCompleteAllTasks = false,
  showActionsColumn = true,
  showViewFormDataButton = false,
}: OwnProps) {
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [formSubmissionTask, setFormSubmissionTask] = useState<Task | null>(
    null
  );

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
      return refreshAtInterval(
        REFRESH_INTERVAL_SECONDS,
        REFRESH_TIMEOUT_SECONDS,
        getTasks
      );
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

  const formSubmissionModal = () => {
    if (formSubmissionTask) {
      return (
        <Modal
          open={!!formSubmissionTask}
          passiveModal
          onRequestClose={() => setFormSubmissionTask(null)}
          modalHeading={`${formSubmissionTask.name_for_display}
              `}
        >
          <div className="indented-content explanatory-message">
            ✅ You completed this form{' '}
            {TimeAgo.inWords(formSubmissionTask.end_in_seconds)}
            <div>
              <Stack orientation="horizontal" gap={2}>
                Guid: {formSubmissionTask.guid}
              </Stack>
            </div>
          </div>
          <hr />
          <CustomForm
            id={formSubmissionTask.guid}
            formData={formSubmissionTask.data}
            schema={formSubmissionTask.form_schema}
            uiSchema={formSubmissionTask.form_ui_schema}
            disabled
          >
            {/* this hides the submit button */}
            {true}
          </CustomForm>
        </Modal>
      );
    }
    return null;
  };

  const getFormSubmissionDataForTask = (
    processInstanceTask: ProcessInstanceTask
  ) => {
    HttpService.makeCallToBackend({
      path: `/tasks/${processInstanceTask.process_instance_id}/${processInstanceTask.task_id}?with_form_data=true`,
      httpMethod: 'GET',
      successCallback: (result: Task) => setFormSubmissionTask(result),
    });
  };

  const processIdRowElement = (processInstanceTask: ProcessInstanceTask) => {
    const modifiedProcessModelIdentifier = modifyProcessIdentifierForPathParam(
      processInstanceTask.process_model_identifier
    );
    return (
      <td>
        <Link
          data-qa="process-instance-show-link-id"
          to={`/admin/process-instances/for-me/${modifiedProcessModelIdentifier}/${processInstanceTask.process_instance_id}`}
          title={`View process instance ${processInstanceTask.process_instance_id}`}
        >
          {processInstanceTask.process_instance_id}
        </Link>
      </td>
    );
  };

  const dealWithProcessCells = (
    rowElements: ReactElement[],
    processInstanceTask: ProcessInstanceTask
  ) => {
    if (showProcessId) {
      rowElements.push(processIdRowElement(processInstanceTask));
    }
    if (showProcessModelIdentifier) {
      const modifiedProcessModelIdentifier =
        modifyProcessIdentifierForPathParam(
          processInstanceTask.process_model_identifier
        );
      rowElements.push(
        <td>
          <Link
            data-qa="process-model-show-link"
            to={`/admin/process-models/${modifiedProcessModelIdentifier}`}
            title={processInstanceTask.process_model_identifier}
          >
            {processInstanceTask.process_model_display_name}
          </Link>
        </td>
      );
    }
  };

  const getTableRow = (processInstanceTask: ProcessInstanceTask) => {
    const taskUrl = `/tasks/${processInstanceTask.process_instance_id}/${processInstanceTask.task_id}`;

    const regex = new RegExp(`\\b(${preferredUsername}|${userEmail})\\b`);
    let hasAccessToCompleteTask = false;
    if (
      canCompleteAllTasks ||
      (processInstanceTask.potential_owner_usernames || '').match(regex)
    ) {
      hasAccessToCompleteTask = true;
    }
    const rowElements: ReactElement[] = [];

    dealWithProcessCells(rowElements, processInstanceTask);

    rowElements.push(
      <td
        title={`task id: ${processInstanceTask.name}, spiffworkflow task guid: ${processInstanceTask.id}`}
      >
        {processInstanceTask.task_title
          ? processInstanceTask.task_title
          : processInstanceTask.task_name}
      </td>
    );
    if (showStartedBy) {
      rowElements.push(
        <td>{processInstanceTask.process_initiator_username}</td>
      );
    }
    if (showWaitingOn) {
      rowElements.push(
        <td>{getWaitingForTableCellComponent(processInstanceTask)}</td>
      );
    }
    if (showDateStarted) {
      rowElements.push(
        <td>
          {convertSecondsToFormattedDateTime(
            processInstanceTask.created_at_in_seconds
          ) || '-'}
        </td>
      );
    }
    if (showLastUpdated) {
      rowElements.push(
        <TableCellWithTimeAgoInWords
          timeInSeconds={processInstanceTask.updated_at_in_seconds}
        />
      );
    }
    if (showActionsColumn) {
      const actions = [];
      if (
        !(
          processInstanceTask.process_instance_status in
          ['suspended', 'completed', 'error']
        ) &&
        !processInstanceTask.completed
      ) {
        actions.push(
          <Button
            variant="primary"
            href={taskUrl}
            disabled={!hasAccessToCompleteTask}
            size="sm"
          >
            Go
          </Button>
        );
      }
      if (showViewFormDataButton) {
        actions.push(
          <Button
            variant="primary"
            onClick={() => getFormSubmissionDataForTask(processInstanceTask)}
          >
            View form
          </Button>
        );
      }
      rowElements.push(<td>{actions}</td>);
    }
    return <tr key={processInstanceTask.id}>{rowElements}</tr>;
  };

  const getTableHeaders = () => {
    let tableHeaders = [];
    if (showProcessId) {
      tableHeaders.push('Id');
    }
    if (showProcessModelIdentifier) {
      tableHeaders.push('Process');
    }
    tableHeaders.push('Task');
    if (showStartedBy) {
      tableHeaders.push('Started By');
    }
    if (showWaitingOn) {
      tableHeaders.push('Waiting For');
    }
    if (showDateStarted) {
      tableHeaders.push('Date Started');
    }
    if (showLastUpdated) {
      tableHeaders.push('Last Updated');
    }
    if (showActionsColumn) {
      tableHeaders = tableHeaders.concat(['Actions']);
    }
    return tableHeaders;
  };

  const buildTable = () => {
    if (!tasks) {
      return null;
    }
    const tableHeaders = getTableHeaders();
    const rows = tasks.map((processInstanceTask: ProcessInstanceTask) => {
      return getTableRow(processInstanceTask);
    });
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
    let tableElement = (
      <div className={paginationClassName}>{buildTable()}</div>
    );
    if (shouldPaginateTable) {
      tableElement = (
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
    }
    return tableElement;
  };

  const tableAndDescriptionElement = () => {
    if (!tableTitle) {
      return null;
    }
    if (showTableDescriptionAsTooltip) {
      return <h2 title={tableDescription}>{tableTitle}</h2>;
    }
    return (
      <>
        <h2>{tableTitle}</h2>
        <p className="data-table-description">{tableDescription}</p>
      </>
    );
  };

  if (tasks && (tasks.length > 0 || hideIfNoTasks === false)) {
    return (
      <>
        {formSubmissionModal()}
        {tableAndDescriptionElement()}
        {tasksComponent()}
      </>
    );
  }
  return null;
}

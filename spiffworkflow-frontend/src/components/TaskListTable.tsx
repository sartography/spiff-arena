import { ReactElement, useEffect, useState } from 'react';
import { Button, Table, Modal, Stack } from '@carbon/react';
import { Link, useSearchParams } from 'react-router-dom';
// @ts-ignore
import { TimeAgo } from '../helpers/timeago';
import UserService from '../services/UserService';
import PaginationForTable from './PaginationForTable';
import {
  getPageInfoFromSearchParams,
  modifyProcessIdentifierForPathParam,
  refreshAtInterval,
} from '../helpers';
import HttpService from '../services/HttpService';
import { PaginationObject, ProcessInstanceTask, Task } from '../interfaces';
import TableCellWithTimeAgoInWords from './TableCellWithTimeAgoInWords';
import CustomForm from './CustomForm';
import InstructionsForEndUser from './InstructionsForEndUser';
import DateAndTimeService from '../services/DateAndTimeService';

type OwnProps = {
  apiPath: string;

  additionalParams?: string;
  autoReload?: boolean;
  canCompleteAllTasks?: boolean;
  defaultPerPage?: number;
  hideIfNoTasks?: boolean;
  paginationClassName?: string;
  paginationQueryParamPrefix?: string;
  shouldPaginateTable?: boolean;
  showActionsColumn?: boolean;
  showCompletedBy?: boolean;
  showDateStarted?: boolean;
  showLastUpdated?: boolean;
  showProcessId?: boolean;
  showProcessModelIdentifier?: boolean;
  showStartedBy?: boolean;
  showTableDescriptionAsTooltip?: boolean;
  showViewFormDataButton?: boolean;
  showWaitingOn?: boolean;
  tableDescription?: string;
  tableTitle?: string;
  textToShowIfEmpty?: string;
};

export default function TaskListTable({
  apiPath,

  additionalParams,
  autoReload = false,
  canCompleteAllTasks = false,
  defaultPerPage = 5,
  hideIfNoTasks = false,
  paginationClassName,
  paginationQueryParamPrefix,
  shouldPaginateTable = true,
  showActionsColumn = true,
  showCompletedBy = false,
  showDateStarted = true,
  showLastUpdated = true,
  showProcessId = true,
  showProcessModelIdentifier = true,
  showStartedBy = true,
  showTableDescriptionAsTooltip = false,
  showViewFormDataButton = false,
  showWaitingOn = true,
  tableDescription,
  tableTitle,
  textToShowIfEmpty,
}: OwnProps) {
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [pagination, setPagination] = useState<PaginationObject | null>(null);
  const [formSubmissionTask, setFormSubmissionTask] = useState<Task | null>(
    null,
  );

  const preferredUsername = UserService.getPreferredUsername();
  const userEmail = UserService.getUserEmail();

  useEffect(() => {
    const getTasks = () => {
      const { page, perPage } = getPageInfoFromSearchParams(
        searchParams,
        defaultPerPage,
        undefined,
        paginationQueryParamPrefix,
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
        DateAndTimeService.REFRESH_INTERVAL_SECONDS,
        DateAndTimeService.REFRESH_TIMEOUT_SECONDS,
        getTasks,
      );
    }
    return undefined;
  }, [
    additionalParams,
    apiPath,
    autoReload,
    defaultPerPage,
    paginationQueryParamPrefix,
    searchParams,
  ]);

  const getWaitingForTableCellComponent = (
    processInstanceTask: ProcessInstanceTask,
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
      // TODO: move this and the code from TaskShow to new component to handle instructions and manual tasks
      let formUiSchema;
      let jsonSchema = formSubmissionTask.form_schema;
      if (formSubmissionTask.typename !== 'UserTask') {
        jsonSchema = {
          type: 'object',
          required: [],
          properties: {
            isManualTask: {
              type: 'boolean',
              title: 'Is ManualTask',
              default: true,
            },
          },
        };
        formUiSchema = {
          isManualTask: {
            'ui:widget': 'hidden',
          },
        };
      } else if (formSubmissionTask.form_ui_schema) {
        formUiSchema = formSubmissionTask.form_ui_schema;
      }
      return (
        <Modal
          open={!!formSubmissionTask}
          passiveModal
          onRequestClose={() => setFormSubmissionTask(null)}
          modalHeading={`${formSubmissionTask.name_for_display}`}
          className="completed-task-modal"
        >
          <div className="indented-content explanatory-message">
            ✅ You completed this task{' '}
            {TimeAgo.inWords(formSubmissionTask.end_in_seconds)}
            <div>
              <Stack orientation="horizontal" gap={2}>
                Guid: {formSubmissionTask.guid}
              </Stack>
            </div>
          </div>
          <hr />
          <div className="with-bottom-margin">
            <InstructionsForEndUser task={formSubmissionTask} allowCollapse />
          </div>
          <CustomForm
            id={formSubmissionTask.guid}
            key={formSubmissionTask.guid}
            formData={formSubmissionTask.data}
            schema={jsonSchema}
            uiSchema={formUiSchema}
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
    processInstanceTask: ProcessInstanceTask,
  ) => {
    HttpService.makeCallToBackend({
      path: `/tasks/${processInstanceTask.process_instance_id}/${processInstanceTask.task_id}?with_form_data=true`,
      httpMethod: 'GET',
      successCallback: (result: Task) => setFormSubmissionTask(result),
    });
  };

  const processIdRowElement = (processInstanceTask: ProcessInstanceTask) => {
    const modifiedProcessModelIdentifier = modifyProcessIdentifierForPathParam(
      processInstanceTask.process_model_identifier,
    );
    return (
      <td>
        <Link
          data-qa="process-instance-show-link-id"
          to={`/process-instances/for-me/${modifiedProcessModelIdentifier}/${processInstanceTask.process_instance_id}`}
          title={`View process instance ${processInstanceTask.process_instance_id}`}
        >
          {processInstanceTask.process_instance_id}
        </Link>
      </td>
    );
  };

  const dealWithProcessCells = (
    rowElements: ReactElement[],
    processInstanceTask: ProcessInstanceTask,
  ) => {
    if (showProcessId) {
      rowElements.push(processIdRowElement(processInstanceTask));
    }
    if (showProcessModelIdentifier) {
      const modifiedProcessModelIdentifier =
        modifyProcessIdentifierForPathParam(
          processInstanceTask.process_model_identifier,
        );
      rowElements.push(
        <td>
          <Link
            data-qa="process-model-show-link"
            to={`/process-models/${modifiedProcessModelIdentifier}`}
            title={processInstanceTask.process_model_identifier}
          >
            {processInstanceTask.process_model_display_name}
          </Link>
        </td>,
      );
    }
  };

  const getActionButtons = (processInstanceTask: ProcessInstanceTask) => {
    const taskUrl = `/tasks/${processInstanceTask.process_instance_id}/${processInstanceTask.task_id}`;
    const regex = new RegExp(`\\b(${preferredUsername}|${userEmail})\\b`);
    let hasAccessToCompleteTask = false;
    if (
      canCompleteAllTasks ||
      (processInstanceTask.potential_owner_usernames || '').match(regex)
    ) {
      hasAccessToCompleteTask = true;
    }

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
        </Button>,
      );
    }
    if (showViewFormDataButton) {
      actions.push(
        <Button
          variant="primary"
          onClick={() => getFormSubmissionDataForTask(processInstanceTask)}
        >
          View task
        </Button>,
      );
    }
    return actions;
  };

  const getTableRow = (processInstanceTask: ProcessInstanceTask) => {
    const rowElements: ReactElement[] = [];

    dealWithProcessCells(rowElements, processInstanceTask);

    rowElements.push(
      <td
        title={`task id: ${processInstanceTask.name}, spiffworkflow task guid: ${processInstanceTask.id}`}
      >
        {processInstanceTask.task_title
          ? processInstanceTask.task_title
          : processInstanceTask.task_name}
      </td>,
    );
    if (showStartedBy) {
      rowElements.push(
        <td>{processInstanceTask.process_initiator_username}</td>,
      );
    }
    if (showWaitingOn) {
      rowElements.push(
        <td>{getWaitingForTableCellComponent(processInstanceTask)}</td>,
      );
    }
    if (showCompletedBy) {
      rowElements.push(<td>{processInstanceTask.completed_by_username}</td>);
    }
    if (showDateStarted) {
      rowElements.push(
        <td>
          {DateAndTimeService.convertSecondsToFormattedDateTime(
            processInstanceTask.created_at_in_seconds,
          ) || '-'}
        </td>,
      );
    }
    if (showLastUpdated) {
      rowElements.push(
        <TableCellWithTimeAgoInWords
          timeInSeconds={processInstanceTask.updated_at_in_seconds}
        />,
      );
    }
    if (showActionsColumn) {
      rowElements.push(<td>{getActionButtons(processInstanceTask)}</td>);
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
      tableHeaders.push('Started by');
    }
    if (showWaitingOn) {
      tableHeaders.push('Waiting for');
    }
    if (showCompletedBy) {
      tableHeaders.push('Completed by');
    }
    if (showDateStarted) {
      tableHeaders.push('Date started');
    }
    if (showLastUpdated) {
      tableHeaders.push('Last updated');
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
      defaultPerPage,
      undefined,
      paginationQueryParamPrefix,
    );
    let tableElement = (
      <div className={paginationClassName}>{buildTable()}</div>
    );
    if (shouldPaginateTable) {
      tableElement = (
        <PaginationForTable
          page={page}
          perPage={perPage}
          perPageOptions={[2, defaultPerPage, 25]}
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

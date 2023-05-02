import { useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import {
  useParams,
  useNavigate,
  Link,
  useSearchParams,
} from 'react-router-dom';
import {
  TrashCan,
  StopOutline,
  PauseOutline,
  PlayOutline,
  InProgress,
  Checkmark,
  Warning,
  // @ts-ignore
} from '@carbon/icons-react';
import {
  Grid,
  Column,
  Button,
  ButtonSet,
  Tag,
  Modal,
  Dropdown,
  Stack,
  Loading,
  // @ts-ignore
} from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ReactDiagramEditor from '../components/ReactDiagramEditor';
import {
  convertSecondsToFormattedDateTime,
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
} from '../helpers';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  EventDefinition,
  PermissionsToCheck,
  ProcessData,
  ProcessInstance,
  ProcessInstanceMetadata,
  Task,
  TaskDefinitionPropertiesJson,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessInstanceClass from '../classes/ProcessInstanceClass';
import TaskListTable from '../components/TaskListTable';
import useAPIError from '../hooks/UseApiError';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceShow({ variant }: OwnProps) {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [tasksCallHadError, setTasksCallHadError] = useState<boolean>(false);
  const [taskToDisplay, setTaskToDisplay] = useState<Task | null>(null);
  const [taskToTimeTravelTo, setTaskToTimeTravelTo] = useState<Task | null>(
    null
  );
  const [taskDataToDisplay, setTaskDataToDisplay] = useState<string>('');
  const [showTaskDataLoading, setShowTaskDataLoading] =
    useState<boolean>(false);

  const [processDataToDisplay, setProcessDataToDisplay] =
    useState<ProcessData | null>(null);
  const [editingTaskData, setEditingTaskData] = useState<boolean>(false);
  const [selectingEvent, setSelectingEvent] = useState<boolean>(false);
  const [eventToSend, setEventToSend] = useState<any>({});
  const [eventPayload, setEventPayload] = useState<string>('{}');
  const [eventTextEditorEnabled, setEventTextEditorEnabled] =
    useState<boolean>(false);
  const [showProcessInstanceMetadata, setShowProcessInstanceMetadata] =
    useState<boolean>(false);

  const { addError, removeError } = useAPIError();
  const unModifiedProcessModelId = unModifyProcessIdentifierForPathParam(
    `${params.process_model_id}`
  );
  const modifiedProcessModelId = params.process_model_id;

  const { targetUris } = useUriListForPermissions();
  const taskListPath =
    variant === 'all'
      ? targetUris.processInstanceTaskListPath
      : targetUris.processInstanceTaskListForMePath;

  const permissionRequestData: PermissionsToCheck = {
    [`${targetUris.processInstanceResumePath}`]: ['POST'],
    [`${targetUris.processInstanceSuspendPath}`]: ['POST'],
    [`${targetUris.processInstanceTerminatePath}`]: ['POST'],
    [targetUris.processInstanceResetPath]: ['POST'],
    [targetUris.messageInstanceListPath]: ['GET'],
    [targetUris.processInstanceActionPath]: ['DELETE'],
    [targetUris.processInstanceLogListPath]: ['GET'],
    [targetUris.processInstanceTaskDataPath]: ['GET', 'PUT'],
    [targetUris.processInstanceSendEventPath]: ['POST'],
    [targetUris.processInstanceCompleteTaskPath]: ['POST'],
    [targetUris.processModelShowPath]: ['PUT'],
    [taskListPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData
  );

  const navigateToProcessInstances = (_result: any) => {
    navigate(
      `/admin/process-instances?process_model_identifier=${unModifiedProcessModelId}`
    );
  };

  let processInstanceShowPageBaseUrl = `/admin/process-instances/for-me/${params.process_model_id}/${params.process_instance_id}`;
  let processInstanceLogListPageBaseUrl = `/admin/logs/for-me/${params.process_model_id}/${params.process_instance_id}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = `/admin/process-instances/${params.process_model_id}/${params.process_instance_id}`;
    processInstanceLogListPageBaseUrl = `/admin/logs/${params.process_model_id}/${params.process_instance_id}`;
  }

  useEffect(() => {
    if (!permissionsLoaded) {
      return undefined;
    }
    const processTaskFailure = () => {
      setTasksCallHadError(true);
    };
    const processTasksSuccess = (results: Task[]) => {
      if (params.to_task_guid) {
        const matchingTask = results.find(
          (task: Task) => task.guid === params.to_task_guid
        );
        if (matchingTask) {
          setTaskToTimeTravelTo(matchingTask);
        }
      }
      setTasks(results);
    };
    let queryParams = '';
    const processIdentifier = searchParams.get('process_identifier');
    if (processIdentifier) {
      queryParams = `?process_identifier=${processIdentifier}`;
    }
    let apiPath = '/process-instances/for-me';
    if (variant === 'all') {
      apiPath = '/process-instances';
    }
    HttpService.makeCallToBackend({
      path: `${apiPath}/${modifiedProcessModelId}/${params.process_instance_id}${queryParams}`,
      successCallback: setProcessInstance,
    });
    let taskParams = '?most_recent_tasks_only=true';
    if (typeof params.to_task_guid !== 'undefined') {
      taskParams = `${taskParams}&to_task_guid=${params.to_task_guid}`;
    }
    const bpmnProcessGuid = searchParams.get('bpmn_process_guid');
    if (bpmnProcessGuid) {
      taskParams = `${taskParams}&bpmn_process_guid=${bpmnProcessGuid}`;
    }
    let taskPath = '';
    if (ability.can('GET', taskListPath)) {
      taskPath = `${taskListPath}${taskParams}`;
    }
    if (taskPath) {
      HttpService.makeCallToBackend({
        path: taskPath,
        successCallback: processTasksSuccess,
        failureCallback: processTaskFailure,
      });
    } else {
      setTasksCallHadError(true);
    }
    return undefined;
  }, [
    targetUris,
    params,
    modifiedProcessModelId,
    permissionsLoaded,
    ability,
    searchParams,
    taskListPath,
    variant,
  ]);

  const deleteProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: targetUris.processInstanceActionPath,
      successCallback: navigateToProcessInstances,
      httpMethod: 'DELETE',
    });
  };

  // to force update the diagram since it could have changed
  const refreshPage = () => {
    window.location.reload();
  };

  const terminateProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceTerminatePath}`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const suspendProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceSuspendPath}`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const resumeProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceResumePath}`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const currentToTaskGuid = () => {
    if (taskToTimeTravelTo) {
      return taskToTimeTravelTo.guid;
    }
    return null;
  };

  // right now this just assume if taskToTimeTravelTo was passed in then
  // this cannot be the active task.
  // we may need a better way to figure this out.
  const showingActiveTask = () => {
    return !taskToTimeTravelTo;
  };

  const queryParams = () => {
    const processIdentifier = searchParams.get('process_identifier');
    const callActivityTaskId = searchParams.get('bpmn_process_guid');
    const queryParamArray = [];
    if (processIdentifier) {
      queryParamArray.push(`process_identifier=${processIdentifier}`);
    }
    if (callActivityTaskId) {
      queryParamArray.push(`bpmn_process_guid=${callActivityTaskId}`);
    }
    let queryParamString = '';
    if (queryParamArray.length > 0) {
      queryParamString = `?${queryParamArray.join('&')}`;
    }
    return queryParamString;
  };

  const completionViewLink = (label: any, taskGuid: string) => {
    return (
      <Link
        reloadDocument
        data-qa="process-instance-step-link"
        to={`${processInstanceShowPageBaseUrl}/${taskGuid}${queryParams()}`}
      >
        {label}
      </Link>
    );
  };

  const returnToProcessInstance = () => {
    window.location.href = `${processInstanceShowPageBaseUrl}${queryParams()}`;
  };

  const resetProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceResetPath}/${currentToTaskGuid()}`,
      successCallback: returnToProcessInstance,
      httpMethod: 'POST',
    });
  };

  const getInfoTag = () => {
    if (!processInstance) {
      return null;
    }
    let lastUpdatedTimeLabel = 'Updated At';
    let lastUpdatedTime = processInstance.updated_at_in_seconds;
    if (processInstance.end_in_seconds) {
      lastUpdatedTimeLabel = 'Completed';
      lastUpdatedTime = processInstance.end_in_seconds;
    }
    const lastUpdatedTimeTag = (
      <Grid condensed fullWidth>
        <Column sm={1} md={1} lg={2} className="grid-list-title">
          {lastUpdatedTimeLabel}:{' '}
        </Column>
        <Column sm={3} md={3} lg={3} className="grid-date">
          {convertSecondsToFormattedDateTime(lastUpdatedTime || 0) || 'N/A'}
        </Column>
      </Grid>
    );

    let statusIcon = <InProgress />;
    if (processInstance.status === 'suspended') {
      statusIcon = <PauseOutline />;
    } else if (processInstance.status === 'complete') {
      statusIcon = <Checkmark />;
    } else if (processInstance.status === 'terminated') {
      statusIcon = <StopOutline />;
    } else if (processInstance.status === 'error') {
      statusIcon = <Warning />;
    }

    return (
      <>
        <Grid condensed fullWidth>
          <Column sm={1} md={1} lg={2} className="grid-list-title">
            Started By:{' '}
          </Column>
          <Column sm={3} md={3} lg={3} className="grid-date">
            {processInstance.process_initiator_username}
          </Column>
        </Grid>
        {processInstance.process_model_with_diagram_identifier ? (
          <Grid condensed fullWidth>
            <Column sm={1} md={1} lg={2} className="grid-list-title">
              Current Diagram:{' '}
            </Column>
            <Column sm={4} md={6} lg={8} className="grid-date">
              <Link
                data-qa="go-to-current-diagram-process-model"
                to={`/admin/process-models/${modifyProcessIdentifierForPathParam(
                  processInstance.process_model_with_diagram_identifier || ''
                )}`}
              >
                {processInstance.process_model_with_diagram_identifier}
              </Link>
            </Column>
          </Grid>
        ) : null}
        <Grid condensed fullWidth>
          <Column sm={1} md={1} lg={2} className="grid-list-title">
            Started:{' '}
          </Column>
          <Column
            sm={3}
            md={3}
            lg={3}
            className="grid-date"
            title={`Created At: ${convertSecondsToFormattedDateTime(
              processInstance.created_at_in_seconds
            )}`}
          >
            {convertSecondsToFormattedDateTime(
              processInstance.start_in_seconds || 0
            )}
          </Column>
        </Grid>
        {lastUpdatedTimeTag}
        <Grid condensed fullWidth>
          <Column sm={1} md={1} lg={2} className="grid-list-title">
            Process model revision:{' '}
          </Column>
          <Column sm={3} md={3} lg={3} className="grid-date">
            {processInstance.bpmn_version_control_identifier} (
            {processInstance.bpmn_version_control_type})
          </Column>
        </Grid>
        <Grid condensed fullWidth>
          <Column sm={1} md={1} lg={2} className="grid-list-title">
            Status:{' '}
          </Column>
          <Column sm={3} md={3} lg={3}>
            <Tag type="gray" size="sm" className="span-tag">
              {processInstance.status} {statusIcon}
            </Tag>
          </Column>
        </Grid>
        <br />
        <Grid condensed fullWidth>
          <Column sm={2} md={2} lg={2}>
            <ButtonSet>
              <Can
                I="GET"
                a={targetUris.processInstanceLogListPath}
                ability={ability}
              >
                <Button
                  size="sm"
                  className="button-white-background"
                  data-qa="process-instance-log-list-link"
                  href={`${processInstanceLogListPageBaseUrl}`}
                >
                  Logs
                </Button>
              </Can>
              <Can
                I="GET"
                a={targetUris.messageInstanceListPath}
                ability={ability}
              >
                <Button
                  size="sm"
                  className="button-white-background"
                  data-qa="process-instance-message-instance-list-link"
                  href={`/admin/messages?process_model_id=${params.process_model_id}&process_instance_id=${params.process_instance_id}`}
                >
                  Messages
                </Button>
              </Can>
              {processInstance.process_metadata &&
              processInstance.process_metadata.length > 0 ? (
                <Button
                  size="sm"
                  className="button-white-background"
                  data-qa="process-instance-show-metadata"
                  onClick={() => {
                    setShowProcessInstanceMetadata(true);
                  }}
                >
                  Details
                </Button>
              ) : null}
            </ButtonSet>
          </Column>
        </Grid>
      </>
    );
  };

  const terminateButton = () => {
    if (
      processInstance &&
      !ProcessInstanceClass.terminalStatuses().includes(processInstance.status)
    ) {
      return (
        <ButtonWithConfirmation
          kind="ghost"
          renderIcon={StopOutline}
          iconDescription="Terminate"
          hasIconOnly
          description={`Terminate Process Instance: ${processInstance.id}`}
          onConfirmation={terminateProcessInstance}
          confirmButtonLabel="Terminate"
        />
      );
    }
    return <div />;
  };

  const suspendButton = () => {
    if (
      processInstance &&
      !ProcessInstanceClass.terminalStatuses()
        .concat(['suspended'])
        .includes(processInstance.status)
    ) {
      return (
        <Button
          onClick={suspendProcessInstance}
          kind="ghost"
          renderIcon={PauseOutline}
          iconDescription="Suspend"
          hasIconOnly
          size="lg"
        />
      );
    }
    return <div />;
  };

  const resumeButton = () => {
    if (processInstance && processInstance.status === 'suspended') {
      return (
        <Button
          onClick={resumeProcessInstance}
          kind="ghost"
          renderIcon={PlayOutline}
          iconDescription="Resume"
          hasIconOnly
          size="lg"
        />
      );
    }
    return <div />;
  };

  const processTaskResult = (result: Task) => {
    if (result == null) {
      setTaskDataToDisplay('');
    } else {
      setTaskDataToDisplay(JSON.stringify(result.data, null, 2));
    }
    setShowTaskDataLoading(false);
  };

  const initializeTaskDataToDisplay = (task: Task | null) => {
    if (
      task &&
      (task.state === 'COMPLETED' || task.state === 'READY') &&
      ability.can('GET', targetUris.processInstanceTaskDataPath)
    ) {
      setShowTaskDataLoading(true);
      HttpService.makeCallToBackend({
        path: `${targetUris.processInstanceTaskDataPath}/${task.guid}`,
        httpMethod: 'GET',
        successCallback: processTaskResult,
        failureCallback: (error: any) => {
          setTaskDataToDisplay(`ERROR: ${error.message}`);
          setShowTaskDataLoading(false);
        },
      });
    } else {
      setTaskDataToDisplay('');
    }
  };

  const handleProcessDataDisplayClose = () => {
    setProcessDataToDisplay(null);
  };

  const processDataDisplayArea = () => {
    if (processDataToDisplay) {
      return (
        <Modal
          open={!!processDataToDisplay}
          passiveModal
          onRequestClose={handleProcessDataDisplayClose}
        >
          <h2>Data Object: {processDataToDisplay.process_data_identifier}</h2>
          <br />
          <p>Value:</p>
          <pre>{JSON.stringify(processDataToDisplay.process_data_value)}</pre>
        </Modal>
      );
    }
    return null;
  };

  const handleProcessDataShowResponse = (processData: ProcessData) => {
    setProcessDataToDisplay(processData);
  };

  const handleClickedDiagramTask = (
    shapeElement: any,
    bpmnProcessIdentifiers: any
  ) => {
    if (shapeElement.type === 'bpmn:DataObjectReference') {
      const dataObjectIdentifer = shapeElement.businessObject.dataObjectRef.id;
      HttpService.makeCallToBackend({
        path: `/process-data/${params.process_model_id}/${params.process_instance_id}/${dataObjectIdentifer}`,
        httpMethod: 'GET',
        successCallback: handleProcessDataShowResponse,
      });
    } else if (tasks) {
      const matchingTask: Task | undefined = tasks.find((task: Task) => {
        return (
          task.bpmn_identifier === shapeElement.id &&
          bpmnProcessIdentifiers.includes(
            task.bpmn_process_definition_identifier
          )
        );
      });
      if (matchingTask) {
        setTaskToDisplay(matchingTask);
        initializeTaskDataToDisplay(matchingTask);
      }
    }
  };

  const handleTaskDataDisplayClose = () => {
    setTaskToDisplay(null);
    initializeTaskDataToDisplay(null);
  };

  const getTaskById = (taskId: string) => {
    if (tasks !== null) {
      return tasks.find((task: Task) => task.guid === taskId) || null;
    }
    return null;
  };

  const processScriptUnitTestCreateResult = (result: any) => {
    console.log('result', result);
  };

  const getParentTaskFromTask = (task: Task) => {
    return task.properties_json.parent;
  };

  const createScriptUnitTest = () => {
    if (taskToDisplay) {
      const previousTask: Task | null = getTaskById(
        getParentTaskFromTask(taskToDisplay)
      );
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/script-unit-tests`,
        httpMethod: 'POST',
        successCallback: processScriptUnitTestCreateResult,
        postBody: {
          bpmn_task_identifier: taskToDisplay.bpmn_identifier,
          input_json: previousTask ? previousTask.data : '',
          expected_output_json: taskToDisplay.data,
        },
      });
    }
  };

  const isActiveTask = (task: Task) => {
    const subprocessTypes = [
      'Subprocess',
      'CallActivity',
      'Transactional Subprocess',
    ];
    return (
      (task.state === 'WAITING' &&
        subprocessTypes.filter((t) => t === task.typename).length > 0) ||
      task.state === 'READY'
    );
  };

  const canEditTaskData = (task: Task) => {
    return (
      processInstance &&
      ability.can('PUT', targetUris.processInstanceTaskDataPath) &&
      isActiveTask(task) &&
      processInstance.status === 'suspended' &&
      showingActiveTask()
    );
  };

  const canSendEvent = (task: Task) => {
    // We actually could allow this for any waiting events
    const taskTypes = ['Event Based Gateway'];
    return (
      processInstance &&
      processInstance.status === 'waiting' &&
      ability.can('POST', targetUris.processInstanceSendEventPath) &&
      taskTypes.filter((t) => t === task.typename).length > 0 &&
      task.state === 'WAITING' &&
      showingActiveTask()
    );
  };

  const canCompleteTask = (task: Task) => {
    return (
      processInstance &&
      processInstance.status === 'suspended' &&
      ability.can('POST', targetUris.processInstanceCompleteTaskPath) &&
      isActiveTask(task) &&
      showingActiveTask()
    );
  };

  const canResetProcess = (task: Task) => {
    return (
      ability.can('POST', targetUris.processInstanceResetPath) &&
      processInstance &&
      processInstance.status === 'suspended' &&
      task.state === 'READY' &&
      !showingActiveTask()
    );
  };

  const getEvents = (task: Task) => {
    const handleMessage = (eventDefinition: EventDefinition) => {
      if (eventDefinition.typename === 'MessageEventDefinition') {
        const newEvent = eventDefinition;
        delete newEvent.message_var;
        newEvent.payload = {};
        return newEvent;
      }
      return eventDefinition;
    };
    if (task.event_definition && task.event_definition.event_definitions)
      return task.event_definition.event_definitions.map((e: EventDefinition) =>
        handleMessage(e)
      );
    if (task.event_definition) return [handleMessage(task.event_definition)];
    return [];
  };

  const cancelUpdatingTask = () => {
    setEditingTaskData(false);
    setSelectingEvent(false);
    initializeTaskDataToDisplay(taskToDisplay);
    setEventPayload('{}');
    removeError();
  };

  const taskDataStringToObject = (dataString: string) => {
    return JSON.parse(dataString);
  };

  const saveTaskDataResult = (_: any) => {
    setEditingTaskData(false);
    const dataObject = taskDataStringToObject(taskDataToDisplay);
    if (taskToDisplay) {
      const taskToDisplayCopy: Task = {
        ...taskToDisplay,
        data: dataObject,
      }; // spread operator
      setTaskToDisplay(taskToDisplayCopy);
    }
    refreshPage();
  };

  const saveTaskData = () => {
    if (!taskToDisplay) {
      return;
    }
    removeError();

    // taskToUse is copy of taskToDisplay, with taskDataToDisplay in data attribute
    const taskToUse: Task = { ...taskToDisplay, data: taskDataToDisplay };
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceTaskDataPath}/${taskToUse.guid}`,
      httpMethod: 'PUT',
      successCallback: saveTaskDataResult,
      failureCallback: addError,
      postBody: {
        new_task_data: taskToUse.data,
      },
    });
  };

  const sendEvent = () => {
    if ('payload' in eventToSend)
      eventToSend.payload = JSON.parse(eventPayload);
    HttpService.makeCallToBackend({
      path: `/send-event/${modifiedProcessModelId}/${params.process_instance_id}`,
      httpMethod: 'POST',
      successCallback: saveTaskDataResult,
      failureCallback: addError,
      postBody: eventToSend,
    });
  };

  const completeTask = (execute: boolean) => {
    if (taskToDisplay) {
      HttpService.makeCallToBackend({
        path: `/task-complete/${modifiedProcessModelId}/${params.process_instance_id}/${taskToDisplay.guid}`,
        httpMethod: 'POST',
        successCallback: returnToProcessInstance,
        postBody: { execute },
      });
    }
  };

  const taskDisplayButtons = (task: Task) => {
    const buttons = [];

    if (
      task.typename === 'Script Task' &&
      ability.can('PUT', targetUris.processModelShowPath)
    ) {
      buttons.push(
        <Button
          data-qa="create-script-unit-test-button"
          onClick={createScriptUnitTest}
        >
          Create Script Unit Test
        </Button>
      );
    }

    if (task.typename === 'CallActivity') {
      const taskDefinitionPropertiesJson: TaskDefinitionPropertiesJson =
        task.task_definition_properties_json;
      buttons.push(
        <Link
          data-qa="go-to-call-activity-result"
          to={`${window.location.pathname}?process_identifier=${taskDefinitionPropertiesJson.spec}&bpmn_process_guid=${task.guid}`}
          target="_blank"
        >
          View Call Activity Diagram
        </Link>
      );
    }

    if (editingTaskData) {
      buttons.push(
        <Button data-qa="save-task-data-button" onClick={saveTaskData}>
          Save
        </Button>
      );
      buttons.push(
        <Button
          data-qa="cancel-task-data-edit-button"
          onClick={cancelUpdatingTask}
        >
          Cancel
        </Button>
      );
    } else if (selectingEvent) {
      buttons.push(
        <Button data-qa="send-event-button" onClick={sendEvent}>
          Send
        </Button>
      );
      buttons.push(
        <Button
          data-qa="cancel-task-data-edit-button"
          onClick={cancelUpdatingTask}
        >
          Cancel
        </Button>
      );
    } else {
      if (canEditTaskData(task)) {
        buttons.push(
          <Button
            data-qa="edit-task-data-button"
            onClick={() => setEditingTaskData(true)}
          >
            Edit
          </Button>
        );
      }
      if (canCompleteTask(task)) {
        buttons.push(
          <Button
            data-qa="mark-task-complete-button"
            onClick={() => completeTask(false)}
          >
            Skip Task
          </Button>
        );
        buttons.push(
          <Button
            data-qa="execute-task-complete-button"
            onClick={() => completeTask(true)}
          >
            Execute Task
          </Button>
        );
      }
      if (canSendEvent(task)) {
        buttons.push(
          <Button
            data-qa="select-event-button"
            onClick={() => setSelectingEvent(true)}
          >
            Send Event
          </Button>
        );
      }
      if (canResetProcess(task)) {
        let titleText =
          'This will reset (rewind) the process to put it into a state as if the execution of the process never went past this task. ';
        titleText += 'Yes, we invented a time machine. ';
        titleText += 'And no, you cannot go back after using this feature.';
        buttons.push(
          <Button
            title={titleText}
            data-qa="reset-process-button"
            onClick={() => resetProcessInstance()}
          >
            Reset Process Here
          </Button>
        );
      }
    }

    return buttons;
  };

  const taskDataContainer = () => {
    let taskDataClassName = '';
    if (taskDataToDisplay.startsWith('ERROR:')) {
      taskDataClassName = 'failure-string';
    }
    return editingTaskData ? (
      <Editor
        height={600}
        width="auto"
        defaultLanguage="json"
        defaultValue={taskDataToDisplay}
        onChange={(value) => setTaskDataToDisplay(value || '')}
      />
    ) : (
      <>
        {showTaskDataLoading ? (
          <Loading className="some-class" withOverlay={false} small />
        ) : null}
        <pre className={taskDataClassName}>{taskDataToDisplay}</pre>
      </>
    );
  };

  const eventSelector = (candidateEvents: any) => {
    const editor = (
      <Editor
        height={300}
        width="auto"
        defaultLanguage="json"
        defaultValue={eventPayload}
        onChange={(value: any) => setEventPayload(value || '{}')}
        options={{ readOnly: !eventTextEditorEnabled }}
      />
    );
    return selectingEvent ? (
      <Stack orientation="vertical">
        <Dropdown
          id="process-instance-select-event"
          titleText="Event"
          label="Select Event"
          items={candidateEvents}
          itemToString={(item: any) => item.name || item.label || item.typename}
          onChange={(value: any) => {
            setEventToSend(value.selectedItem);
            setEventTextEditorEnabled(
              value.selectedItem.typename === 'MessageEventDefinition'
            );
          }}
        />
        {editor}
      </Stack>
    ) : (
      taskDataContainer()
    );
  };

  const processInstanceMetadataArea = () => {
    if (
      !processInstance ||
      (processInstance.process_metadata &&
        processInstance.process_metadata.length < 1)
    ) {
      return null;
    }
    const metadataComponents: any[] = [];
    (processInstance.process_metadata || []).forEach(
      (processInstanceMetadata: ProcessInstanceMetadata) => {
        metadataComponents.push(
          <Grid condensed fullWidth>
            <Column sm={3} md={3} lg={5} className="grid-list-title">
              {processInstanceMetadata.key}
            </Column>
            <Column sm={3} md={3} lg={3} className="grid-date">
              {processInstanceMetadata.value}
            </Column>
          </Grid>
        );
      }
    );
    return (
      <Modal
        open={showProcessInstanceMetadata}
        modalHeading="Details"
        passiveModal
        onRequestClose={() => setShowProcessInstanceMetadata(false)}
      >
        {metadataComponents}
      </Modal>
    );
  };

  const taskUpdateDisplayArea = () => {
    if (!taskToDisplay) {
      return null;
    }
    const taskToUse: Task = { ...taskToDisplay, data: taskDataToDisplay };
    const candidateEvents: any = getEvents(taskToUse);
    if (taskToDisplay) {
      let taskTitleText = taskToUse.guid;
      if (taskToUse.bpmn_name) {
        taskTitleText += ` (${taskToUse.bpmn_name})`;
      }
      return (
        <Modal
          open={!!taskToUse}
          passiveModal
          onRequestClose={handleTaskDataDisplayClose}
        >
          <Stack orientation="horizontal" gap={2}>
            <span title={taskTitleText}>{taskToUse.bpmn_identifier}</span> (
            {taskToUse.typename}
            ): {taskToUse.state}
            {taskDisplayButtons(taskToUse)}
          </Stack>
          <div>
            <Stack orientation="horizontal" gap={2}>
              Guid: {taskToUse.guid}
            </Stack>
          </div>
          {taskToUse.state === 'COMPLETED' ? (
            <div>
              <Stack orientation="horizontal" gap={2}>
                {completionViewLink(
                  'View process instance at the time when this task was active.',
                  taskToUse.guid
                )}
              </Stack>
              <br />
              <br />
            </div>
          ) : null}
          {selectingEvent
            ? eventSelector(candidateEvents)
            : taskDataContainer()}
        </Modal>
      );
    }
    return null;
  };

  const buttonIcons = () => {
    if (!processInstance) {
      return null;
    }
    const elements = [];
    if (ability.can('POST', `${targetUris.processInstanceTerminatePath}`)) {
      elements.push(terminateButton());
    }
    if (ability.can('POST', `${targetUris.processInstanceSuspendPath}`)) {
      elements.push(suspendButton());
    }
    if (ability.can('POST', `${targetUris.processInstanceResumePath}`)) {
      elements.push(resumeButton());
    }
    if (
      ability.can('DELETE', targetUris.processInstanceActionPath) &&
      ProcessInstanceClass.terminalStatuses().includes(processInstance.status)
    ) {
      elements.push(
        <ButtonWithConfirmation
          data-qa="process-instance-delete"
          kind="ghost"
          renderIcon={TrashCan}
          iconDescription="Delete"
          hasIconOnly
          description={`Delete Process Instance: ${processInstance.id}`}
          onConfirmation={deleteProcessInstance}
          confirmButtonLabel="Delete"
        />
      );
    }
    return elements;
  };

  const viewMostRecentStateComponent = () => {
    if (!taskToTimeTravelTo) {
      return null;
    }
    const title = `${taskToTimeTravelTo.id}: ${taskToTimeTravelTo.guid}: ${taskToTimeTravelTo.bpmn_identifier}`;
    return (
      <>
        <Grid condensed fullWidth>
          <Column md={8} lg={16} sm={4}>
            <p>
              Viewing process instance at the time when{' '}
              <span title={title}>
                <strong>
                  {taskToTimeTravelTo.bpmn_name ||
                    taskToTimeTravelTo.bpmn_identifier}
                </strong>
              </span>{' '}
              was active.{' '}
              <Link
                reloadDocument
                data-qa="process-instance-view-active-task-link"
                to={processInstanceShowPageBaseUrl}
              >
                View current process instance state.
              </Link>
            </p>
          </Column>
        </Grid>
        <br />
      </>
    );
  };

  if (processInstance && (tasks || tasksCallHadError)) {
    const processModelId = unModifyProcessIdentifierForPathParam(
      params.process_model_id ? params.process_model_id : ''
    );

    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/admin'],
            {
              entityToExplode: processModelId,
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [`Process Instance Id: ${processInstance.id}`],
          ]}
        />
        <Stack orientation="horizontal" gap={1}>
          <h1 className="with-icons">
            Process Instance Id: {processInstance.id}
          </h1>
          {buttonIcons()}
        </Stack>
        <br />
        <br />
        <Grid condensed fullWidth>
          <Column md={6} lg={8} sm={4}>
            <TaskListTable
              apiPath="/tasks"
              additionalParams={`process_instance_id=${processInstance.id}`}
              tableTitle="Tasks I can complete"
              tableDescription="These are tasks that can be completed by you, either because they were assigned to a group you are in, or because they were assigned directly to you."
              paginationClassName="with-large-bottom-margin"
              textToShowIfEmpty="There are no tasks you can complete for this process instance."
              shouldPaginateTable={false}
              showProcessModelIdentifier={false}
              showProcessId={false}
              showStartedBy={false}
              showTableDescriptionAsTooltip
              showDateStarted={false}
              showLastUpdated={false}
              hideIfNoTasks
              canCompleteAllTasks
            />
          </Column>
        </Grid>
        {getInfoTag()}
        <br />
        {taskUpdateDisplayArea()}
        {processDataDisplayArea()}
        {processInstanceMetadataArea()}
        <br />
        {viewMostRecentStateComponent()}
        <ReactDiagramEditor
          processModelId={processModelId || ''}
          diagramXML={processInstance.bpmn_xml_file_contents || ''}
          fileName={processInstance.bpmn_xml_file_contents || ''}
          tasks={tasks}
          diagramType="readonly"
          onElementClick={handleClickedDiagramTask}
        />

        <div id="diagram-container" />
      </>
    );
  }
  return null;
}

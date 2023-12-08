import { useCallback, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import {
  useParams,
  useNavigate,
  Link,
  useSearchParams,
} from 'react-router-dom';
import {
  Send,
  Checkmark,
  Edit,
  InProgress,
  PauseOutline,
  UserFollow,
  Play,
  PlayOutline,
  Reset,
  RuleDraft,
  SkipForward,
  StopOutline,
  TrashCan,
  Warning,
  Link as LinkIcon,
} from '@carbon/icons-react';
import {
  Accordion,
  AccordionItem,
  Grid,
  Column,
  Button,
  ButtonSet,
  Tag,
  Modal,
  Dropdown,
  Stack,
  Loading,
  Tabs,
  Tab,
  TabList,
  TabPanels,
  TabPanel,
} from '@carbon/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ReactDiagramEditor from '../components/ReactDiagramEditor';
import {
  getLastMilestoneFromProcessInstance,
  HUMAN_TASK_TYPES,
  modifyProcessIdentifierForPathParam,
  truncateString,
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  ErrorForDisplay,
  EventDefinition,
  KeyboardShortcuts,
  PermissionsToCheck,
  ProcessData,
  ProcessInstance,
  Task,
  TaskDefinitionPropertiesJson,
  User,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessInstanceClass from '../classes/ProcessInstanceClass';
import TaskListTable from '../components/TaskListTable';
import useAPIError from '../hooks/UseApiError';
import UserSearch from '../components/UserSearch';
import ProcessInstanceLogList from '../components/ProcessInstanceLogList';
import MessageInstanceList from '../components/MessageInstanceList';
import {
  childrenForErrorObject,
  errorForDisplayFromString,
} from '../components/ErrorDisplay';
import { Notification } from '../components/Notification';
import DateAndTimeService from '../services/DateAndTimeService';
import ProcessInstanceCurrentTaskInfo from '../components/ProcessInstanceCurrentTaskInfo';
import useKeyboardShortcut from '../hooks/useKeyboardShortcut';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceShow({ variant }: OwnProps) {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();

  const eventsThatNeedPayload = ['MessageEventDefinition'];

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

  const [addingPotentialOwners, setAddingPotentialOwners] =
    useState<boolean>(false);
  const [additionalPotentialOwners, setAdditionalPotentialOwners] = useState<
    User[] | null
  >(null);

  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const [selectedTaskTabSubTab, setSelectedTaskTabSubTab] = useState<number>(0);
  const [copiedShortLinkToClipboard, setCopiedShortLinkToClipboard] =
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
    [targetUris.processInstanceActionPath]: ['DELETE', 'GET', 'POST'],
    [targetUris.processInstanceLogListPath]: ['GET'],
    [targetUris.processInstanceTaskAssignPath]: ['POST'],
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
      `/process-instances?process_model_identifier=${unModifiedProcessModelId}`
    );
  };

  const onProcessInstanceRun = (processInstanceResult: ProcessInstance) => {
    const processInstanceId = processInstanceResult.id;
    if (processInstanceResult.process_model_uses_queued_execution) {
      navigate(
        `/process-instances/${modifiedProcessModelId}/${processInstanceId}/progress`
      );
    } else {
      navigate(
        `/process-instances/${modifiedProcessModelId}/${processInstanceId}/interstitial`
      );
    }
  };

  const forceRunProcessInstance = () => {
    if (ability.can('POST', targetUris.processInstanceActionPath)) {
      HttpService.makeCallToBackend({
        path: `${targetUris.processInstanceActionPath}/run?force_run=true`,
        successCallback: onProcessInstanceRun,
        httpMethod: 'POST',
      });
    }
  };

  const keyboardShortcuts: KeyboardShortcuts = {
    'f,r,enter': {
      function: forceRunProcessInstance,
      label: 'Force run process instance',
    },
  };
  const keyboardShortcutArea = useKeyboardShortcut(keyboardShortcuts);

  let processInstanceShowPageBaseUrl = `/process-instances/for-me/${params.process_model_id}/${params.process_instance_id}`;
  const processInstanceShowPageBaseUrlAllVariant = `/process-instances/${params.process_model_id}/${params.process_instance_id}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = processInstanceShowPageBaseUrlAllVariant;
  }

  const handleAddErrorInUseEffect = useCallback((value: ErrorForDisplay) => {
    addError(value);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const getActionableTaskList = useCallback(() => {
    const processTaskFailure = (result: any) => {
      setTasksCallHadError(true);
      handleAddErrorInUseEffect(result);
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
  }, [
    ability,
    handleAddErrorInUseEffect,
    params.to_task_guid,
    searchParams,
    taskListPath,
  ]);

  const getProcessInstance = useCallback(() => {
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
  }, [params, modifiedProcessModelId, searchParams, variant]);

  useEffect(() => {
    if (processInstance) {
      setPageTitle([
        processInstance.process_model_display_name,
        `Process Instance ${processInstance.id}`,
      ]);
    }
    return undefined;
  }, [processInstance]);

  useEffect(() => {
    if (!permissionsLoaded) {
      return undefined;
    }
    getProcessInstance();
    getActionableTaskList();

    if (searchParams.get('tab')) {
      setSelectedTabIndex(parseInt(searchParams.get('tab') || '0', 10));
    }
    if (searchParams.get('taskSubTab')) {
      setSelectedTaskTabSubTab(
        parseInt(searchParams.get('taskSubTab') || '0', 10)
      );
    }
    return undefined;
  }, [
    permissionsLoaded,
    getActionableTaskList,
    getProcessInstance,
    searchParams,
  ]);

  const updateSearchParams = (value: string, key: string) => {
    if (value !== undefined) {
      searchParams.set(key, value);
    } else {
      searchParams.delete(key);
    }
    setSearchParams(searchParams);
  };

  const deleteProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: targetUris.processInstanceActionPath,
      successCallback: navigateToProcessInstances,
      httpMethod: 'DELETE',
    });
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

  // to force update the diagram since it could have changed
  const refreshPage = () => {
    // redirect to the all variant page if possible to avoid potential user/task association issues.
    // such as terminating a process instance with a task that the current user is assigned to which
    // will remove the task assigned to them and could potentially remove that users association to the process instance
    if (ability.can('GET', targetUris.processInstanceActionPath)) {
      window.location.href = `${processInstanceShowPageBaseUrlAllVariant}${queryParams()}`;
    } else {
      window.location.reload();
    }
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
    let lastUpdatedTimeLabel = 'Updated';
    let lastUpdatedTime = processInstance.task_updated_at_in_seconds;
    if (processInstance.end_in_seconds) {
      lastUpdatedTimeLabel = 'Completed';
      lastUpdatedTime = processInstance.end_in_seconds;
    }
    const lastUpdatedTimeTag = (
      <dl>
        <dt>{lastUpdatedTimeLabel}:</dt>
        <dd>
          {DateAndTimeService.convertSecondsToFormattedDateTime(
            lastUpdatedTime || 0
          ) || 'N/A'}
        </dd>
      </dl>
    );

    let statusIcon = <InProgress />;
    let statusColor = 'gray';
    if (processInstance.status === 'suspended') {
      statusIcon = <PauseOutline />;
    } else if (processInstance.status === 'complete') {
      statusIcon = <Checkmark />;
      statusColor = 'green';
    } else if (processInstance.status === 'terminated') {
      statusIcon = <StopOutline />;
    } else if (processInstance.status === 'error') {
      statusIcon = <Warning />;
      statusColor = 'red';
    }

    const [lastMilestoneFullValue, lastMilestoneTruncatedValue] =
      getLastMilestoneFromProcessInstance(
        processInstance,
        processInstance.last_milestone_bpmn_name
      );

    return (
      <Grid condensed fullWidth className="megacondensed">
        <Column sm={4} md={4} lg={5}>
          <dl>
            <dt>Status:</dt>
            <dd>
              <Tag
                type={statusColor}
                size="sm"
                className="tag-within-dl process-instance-status"
              >
                {processInstance.status} {statusIcon}
              </Tag>
            </dd>
          </dl>
          <dl>
            <dt>Started by:</dt>
            <dd> {processInstance.process_initiator_username}</dd>
          </dl>
          {processInstance.process_model_with_diagram_identifier ? (
            <dl>
              <dt>Current diagram: </dt>
              <dd>
                <Link
                  data-qa="go-to-current-diagram-process-model"
                  to={`/process-models/${modifyProcessIdentifierForPathParam(
                    processInstance.process_model_with_diagram_identifier || ''
                  )}`}
                >
                  {processInstance.process_model_with_diagram_identifier}
                </Link>
              </dd>
            </dl>
          ) : null}
          <dl>
            <dt>Started:</dt>
            <dd>
              {DateAndTimeService.convertSecondsToFormattedDateTime(
                processInstance.start_in_seconds || 0
              )}
            </dd>
          </dl>
          {lastUpdatedTimeTag}
          <dl>
            <dt>Last milestone:</dt>
            <dd title={lastMilestoneFullValue}>
              {lastMilestoneTruncatedValue}
            </dd>
          </dl>
          <dl>
            <dt>Revision:</dt>
            <dd>
              {processInstance.bpmn_version_control_identifier} (
              {processInstance.bpmn_version_control_type})
            </dd>
          </dl>
        </Column>
        <Column sm={4} md={4} lg={8}>
          {(processInstance.process_metadata || []).map(
            (processInstanceMetadata) => (
              <dl className="metadata-display">
                <dt title={processInstanceMetadata.key}>
                  {truncateString(processInstanceMetadata.key, 50)}:
                </dt>
                <dd>{processInstanceMetadata.value}</dd>
              </dl>
            )
          )}
        </Column>
      </Grid>
    );
  };

  const copyProcessInstanceShortLink = () => {
    if (processInstance) {
      const piShortLink = `${window.location.origin}/i/${processInstance.id}`;
      navigator.clipboard.writeText(piShortLink);
      setCopiedShortLinkToClipboard(true);
    }
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

  // you cannot suspend an instance that is done. except if it has status error, since
  // you might want to perform admin actions to recover from an errored instance.
  const suspendButton = () => {
    if (
      processInstance &&
      !ProcessInstanceClass.nonErrorTerminalStatuses()
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

  const copyProcessInstanceShortLinkButton = () => {
    return (
      <Button
        onClick={copyProcessInstanceShortLink}
        kind="ghost"
        renderIcon={LinkIcon}
        iconDescription="Copy shareable short link"
        hasIconOnly
        size="lg"
      />
    );
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

  const deleteButton = () => {
    if (
      processInstance &&
      ProcessInstanceClass.terminalStatuses().includes(processInstance.status)
    ) {
      return (
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
      (task.state === 'COMPLETED' ||
        task.state === 'ERROR' ||
        task.state === 'READY') &&
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
      let bodyComponent = (
        <>
          <p>Value:</p>
          <pre>{JSON.stringify(processDataToDisplay.process_data_value)}</pre>
        </>
      );
      if (processDataToDisplay.authorized === false) {
        bodyComponent = (
          <>
            {childrenForErrorObject(
              errorForDisplayFromString(processDataToDisplay.process_data_value)
            )}
          </>
        );
      }
      return (
        <Modal
          open={!!processDataToDisplay}
          passiveModal
          onRequestClose={handleProcessDataDisplayClose}
        >
          <h2>Data Object: {processDataToDisplay.process_data_identifier}</h2>
          <br />
          {bodyComponent}
        </Modal>
      );
    }
    return null;
  };

  const handleProcessDataShowResponse = (processData: ProcessData) => {
    setProcessDataToDisplay(processData);
  };

  const handleProcessDataShowReponseUnauthorized = (
    dataObjectIdentifer: string,
    result: any
  ) => {
    const processData: ProcessData = {
      process_data_identifier: dataObjectIdentifer,
      process_data_value: result.message,
      authorized: false,
    };
    setProcessDataToDisplay(processData);
  };

  const makeProcessDataCallFromShapeElement = (shapeElement: any) => {
    const { dataObjectRef } = shapeElement.businessObject;
    let category = 'default';
    if ('extensionElements' in dataObjectRef) {
      const categoryExtension = dataObjectRef.extensionElements.values.find(
        (extension: any) => {
          return extension.$type === 'spiffworkflow:category';
        }
      );
      if (categoryExtension) {
        category = categoryExtension.$body;
      }
    }
    const dataObjectIdentifer = dataObjectRef.id;
    const parentProcess = shapeElement.businessObject.$parent;
    const processIdentifier = parentProcess.id;

    let additionalParams = '';
    if (tasks) {
      const matchingTask: Task | undefined = tasks.find((task: Task) => {
        return task.bpmn_identifier === processIdentifier;
      });
      if (matchingTask) {
        additionalParams = `?process_identifier=${processIdentifier}&bpmn_process_guid=${matchingTask.guid}`;
      }
    }
    HttpService.makeCallToBackend({
      path: `/process-data/${category}/${params.process_model_id}/${dataObjectIdentifer}/${params.process_instance_id}${additionalParams}`,
      httpMethod: 'GET',
      successCallback: handleProcessDataShowResponse,
      failureCallback: addError,
      onUnauthorized: (result: any) =>
        handleProcessDataShowReponseUnauthorized(dataObjectIdentifer, result),
    });
  };

  const handleClickedDiagramTask = (
    shapeElement: any,
    bpmnProcessIdentifiers: any
  ) => {
    if (shapeElement.type === 'bpmn:DataObjectReference') {
      makeProcessDataCallFromShapeElement(shapeElement);
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

  const resetTaskActionDetails = () => {
    setEditingTaskData(false);
    setSelectingEvent(false);
    setAddingPotentialOwners(false);
    initializeTaskDataToDisplay(taskToDisplay);
    setEventPayload('{}');
    setAdditionalPotentialOwners(null);
    removeError();
  };

  const handleTaskDataDisplayClose = () => {
    setTaskToDisplay(null);
    initializeTaskDataToDisplay(null);
    if (editingTaskData || selectingEvent || addingPotentialOwners) {
      resetTaskActionDetails();
    }
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
      task.state === 'READY' ||
      (processInstance &&
        processInstance.status === 'suspended' &&
        task.state === 'ERROR')
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
    const taskTypes = ['EventBasedGateway'];
    return (
      !selectingEvent &&
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

  const canAddPotentialOwners = (task: Task) => {
    return (
      HUMAN_TASK_TYPES.includes(task.typename) &&
      processInstance &&
      processInstance.status === 'suspended' &&
      ability.can('POST', targetUris.processInstanceTaskAssignPath) &&
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
      if (eventsThatNeedPayload.includes(eventDefinition.typename)) {
        const newEvent = eventDefinition;
        delete newEvent.message_var;
        newEvent.payload = {};
        return newEvent;
      }
      return eventDefinition;
    };
    const eventDefinition =
      task.task_definition_properties_json.event_definition;
    if (eventDefinition && eventDefinition.event_definitions)
      return eventDefinition.event_definitions.map((e: EventDefinition) =>
        handleMessage(e)
      );
    if (eventDefinition) return [handleMessage(eventDefinition)];
    return [];
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

  const addPotentialOwners = () => {
    if (!additionalPotentialOwners) {
      return;
    }
    if (!taskToDisplay) {
      return;
    }
    removeError();

    const userIds = additionalPotentialOwners.map((user: User) => user.id);

    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceTaskAssignPath}/${taskToDisplay.guid}`,
      httpMethod: 'POST',
      successCallback: resetTaskActionDetails,
      failureCallback: addError,
      postBody: {
        user_ids: userIds,
      },
    });
  };

  const sendEvent = () => {
    if ('payload' in eventToSend)
      eventToSend.payload = JSON.parse(eventPayload);
    HttpService.makeCallToBackend({
      path: targetUris.processInstanceSendEventPath,
      httpMethod: 'POST',
      successCallback: refreshPage,
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
    if (editingTaskData || addingPotentialOwners || selectingEvent) {
      return null;
    }

    if (
      task.typename === 'ScriptTask' &&
      ability.can('PUT', targetUris.processModelShowPath)
    ) {
      buttons.push(
        <Button
          kind="ghost"
          align="top-left"
          renderIcon={RuleDraft}
          iconDescription="Create Script Unit Test"
          hasIconOnly
          data-qa="create-script-unit-test-button"
          onClick={createScriptUnitTest}
        />
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

    if (canEditTaskData(task)) {
      buttons.push(
        <Button
          kind="ghost"
          renderIcon={Edit}
          align="top-left"
          iconDescription="Edit Task Data"
          hasIconOnly
          data-qa="edit-task-data-button"
          onClick={() => setEditingTaskData(true)}
        />
      );
    }
    if (canAddPotentialOwners(task)) {
      buttons.push(
        <Button
          kind="ghost"
          renderIcon={UserFollow}
          align="top-left"
          iconDescription="Assign user"
          title="Allow an additional user to complete this task"
          hasIconOnly
          data-qa="add-potential-owners-button"
          onClick={() => setAddingPotentialOwners(true)}
        />
      );
    }
    if (canCompleteTask(task)) {
      buttons.push(
        <Button
          kind="ghost"
          renderIcon={Play}
          align="top-left"
          iconDescription="Execute Task"
          hasIconOnly
          data-qa="execute-task-complete-button"
          onClick={() => completeTask(true)}
        >
          Execute Task
        </Button>
      );
      buttons.push(
        <Button
          kind="ghost"
          renderIcon={SkipForward}
          align="top-left"
          iconDescription="Skip Task"
          hasIconOnly
          data-qa="mark-task-complete-button"
          onClick={() => completeTask(false)}
        >
          Skip Task
        </Button>
      );
    }
    if (canSendEvent(task)) {
      buttons.push(
        <Button
          kind="ghost"
          renderIcon={Send}
          align="top-left"
          iconDescription="Send Event"
          hasIconOnly
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
      titleText +=
        'And no, you cannot change your mind after using this feature.';
      buttons.push(
        <Button
          kind="ghost"
          renderIcon={Reset}
          align="top-left"
          hasIconOnly
          iconDescription="Reset Process Here"
          title={titleText}
          data-qa="reset-process-button"
          onClick={() => resetProcessInstance()}
        />
      );
    }
    return buttons;
  };

  const taskDataContainer = () => {
    let taskDataClassName = '';
    if (taskDataToDisplay.startsWith('ERROR:')) {
      taskDataClassName = 'failure-string';
    }
    const numberOfLines = taskDataToDisplay.split('\n').length;
    let heightInEm = numberOfLines + 5;
    let scrollEnabled = false;
    let minimapEnabled = false;
    if (heightInEm > 30) {
      heightInEm = 30;
      scrollEnabled = true;
      minimapEnabled = true;
    }
    let taskDataHeader = 'Task data';
    let editorReadOnly = true;
    let taskDataHeaderClassName = 'with-half-rem-bottom-margin';

    if (editingTaskData) {
      editorReadOnly = false;
      taskDataHeader = 'Edit task data';
      taskDataHeaderClassName = 'task-data-details-header';
    }

    if (!taskDataToDisplay) {
      return null;
    }

    return (
      <>
        {showTaskDataLoading ? (
          <Loading className="some-class" withOverlay={false} small />
        ) : null}
        {taskDataClassName !== '' ? (
          <pre className={taskDataClassName}>{taskDataToDisplay}</pre>
        ) : (
          <>
            <h3 className={taskDataHeaderClassName}>{taskDataHeader}</h3>
            <Editor
              height={`${heightInEm}rem`}
              width="auto"
              defaultLanguage="json"
              value={taskDataToDisplay}
              onChange={(value) => {
                setTaskDataToDisplay(value || '');
              }}
              options={{
                readOnly: editorReadOnly,
                scrollBeyondLastLine: scrollEnabled,
                minimap: { enabled: minimapEnabled },
              }}
            />
          </>
        )}
      </>
    );
  };

  const potentialOwnerSelector = () => {
    return (
      <Stack orientation="vertical">
        <h3 className="task-data-details-header">Update task ownership</h3>
        <div className="indented-content">
          <p className="explanatory-message with-tiny-bottom-margin">
            Select a user who should be allowed to complete this task
          </p>
          <UserSearch
            className="modal-dropdown"
            onSelectedUser={(user: User) => {
              setAdditionalPotentialOwners([user]);
            }}
          />
        </div>
      </Stack>
    );
  };

  const eventSelector = (candidateEvents: any) => {
    let editor = null;
    let className = 'modal-dropdown';
    if (eventTextEditorEnabled) {
      className = '';
      editor = (
        <Editor
          height={300}
          width="auto"
          defaultLanguage="json"
          defaultValue={eventPayload}
          onChange={(value: any) => setEventPayload(value || '{}')}
          options={{ readOnly: !eventTextEditorEnabled }}
        />
      );
    }
    return (
      <Stack orientation="vertical">
        <h3 className="task-data-details-header">Choose event to send</h3>
        <div className="indented-content">
          <p className="explanatory-message with-tiny-bottom-margin">
            Select an event to send. A message event will require a body as
            well.
          </p>
          <Dropdown
            id="process-instance-select-event"
            className={className}
            label="Select Event"
            items={candidateEvents}
            itemToString={(item: any) =>
              item.name || item.label || item.typename
            }
            onChange={(value: any) => {
              setEventToSend(value.selectedItem);
              setEventTextEditorEnabled(
                eventsThatNeedPayload.includes(value.selectedItem.typename)
              );
            }}
          />
          {editor}
        </div>
      </Stack>
    );
  };

  const taskActionDetails = () => {
    if (!taskToDisplay) {
      return null;
    }
    let dataArea = taskDataContainer();
    if (selectingEvent) {
      const candidateEvents: any = getEvents(taskToDisplay);
      dataArea = eventSelector(candidateEvents);
    } else if (addingPotentialOwners) {
      dataArea = potentialOwnerSelector();
    }
    return dataArea;
  };

  const switchToTask = (taskId: string) => {
    if (tasks) {
      const task = tasks.find((t: Task) => t.guid === taskId);
      if (task) {
        setTaskToDisplay(task);
        initializeTaskDataToDisplay(task);
      }
    }
  };

  const multiInstanceSelector = () => {
    if (!taskToDisplay || !taskToDisplay.runtime_info) {
      return null;
    }

    const clickAction = (item: any) => {
      return () => {
        switchToTask(taskToDisplay.runtime_info.instance_map[item]);
      };
    };
    const createButtonSet = (instances: string[]) => {
      return (
        <ButtonSet stacked>
          {instances.map((v: any) => (
            <Button kind="ghost" onClick={clickAction(v)}>
              {v}
            </Button>
          ))}
        </ButtonSet>
      );
    };

    if (
      taskToDisplay.typename === 'ParallelMultiInstanceTask' ||
      taskToDisplay.typename === 'SequentialMultiInstanceTask'
    ) {
      let completedInstances = null;
      if (taskToDisplay.runtime_info.completed.length > 0) {
        completedInstances = createButtonSet(
          taskToDisplay.runtime_info.completed
        );
      }
      let runningInstances = null;
      if (taskToDisplay.runtime_info.running.length > 0) {
        runningInstances = createButtonSet(taskToDisplay.runtime_info.running);
      }
      let futureInstances = null;
      if (taskToDisplay.runtime_info.future.length > 0) {
        futureInstances = createButtonSet(taskToDisplay.runtime_info.future);
      }

      return (
        <Accordion>
          <AccordionItem title="Completed instances">
            {completedInstances}
          </AccordionItem>
          <AccordionItem title="Running instances">
            {runningInstances}
          </AccordionItem>
          <AccordionItem title="Future instances">
            {futureInstances}
          </AccordionItem>
        </Accordion>
      );
    }
    if (taskToDisplay.typename === 'StandardLoopTask') {
      const buttons = [];
      for (
        let i = 0;
        i < taskToDisplay.runtime_info.iterations_completed;
        i += 1
      )
        buttons.push(
          <Button kind="ghost" onClick={clickAction(i)}>
            {i}
          </Button>
        );
      let text = 'Loop iterations';
      if (
        typeof taskToDisplay.runtime_info.iterations_remaining !== 'undefined'
      )
        text += ` (${taskToDisplay.runtime_info.iterations_remaining} remaining)`;
      return (
        <div>
          <div>{text}</div>
          <div>{buttons}</div>
        </div>
      );
    }
    return null;
  };

  const taskUpdateDisplayArea = () => {
    if (!taskToDisplay) {
      return null;
    }
    const taskToUse: Task = { ...taskToDisplay, data: taskDataToDisplay };

    let primaryButtonText = 'Close';
    let secondaryButtonText = null;
    let onRequestSubmit = handleTaskDataDisplayClose;
    let onSecondarySubmit = handleTaskDataDisplayClose;
    let dangerous = false;
    if (editingTaskData) {
      primaryButtonText = 'Save';
      secondaryButtonText = 'Cancel';
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = saveTaskData;
      dangerous = true;
    } else if (selectingEvent) {
      primaryButtonText = 'Send';
      secondaryButtonText = 'Cancel';
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = sendEvent;
      dangerous = true;
    } else if (addingPotentialOwners) {
      primaryButtonText = 'Add';
      secondaryButtonText = 'Cancel';
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = addPotentialOwners;
      dangerous = true;
    }
    if (taskToUse.runtime_info) {
      if (typeof taskToUse.runtime_info.instance !== 'undefined') {
        secondaryButtonText = 'Return to MultiInstance Task';
        onSecondarySubmit = () => {
          switchToTask(taskToUse.properties_json.parent);
        };
      } else if (typeof taskToUse.runtime_info.iteration !== 'undefined') {
        secondaryButtonText = 'Return to Loop Task';
        onSecondarySubmit = () => {
          switchToTask(taskToUse.properties_json.parent);
        };
      }
    }

    return (
      <Modal
        open={!!taskToUse}
        danger={dangerous}
        primaryButtonText={primaryButtonText}
        secondaryButtonText={secondaryButtonText}
        onRequestClose={handleTaskDataDisplayClose}
        onSecondarySubmit={onSecondarySubmit}
        onRequestSubmit={onRequestSubmit}
        modalHeading={`${taskToUse.bpmn_identifier} (${taskToUse.typename}
              ): ${taskToUse.state}`}
      >
        <div className="indented-content explanatory-message">
          {taskToUse.bpmn_name ? (
            <div>
              <Stack orientation="horizontal" gap={2}>
                Name: {taskToUse.bpmn_name}
              </Stack>
            </div>
          ) : null}

          <div>
            <Stack orientation="horizontal" gap={2}>
              Guid: {taskToUse.guid}
            </Stack>
          </div>
        </div>
        {taskDisplayButtons(taskToUse)}
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
        {taskActionDetails()}
        {multiInstanceSelector()}
      </Modal>
    );
  };

  const buttonIcons = () => {
    if (!processInstance) {
      return null;
    }
    const elements = [];
    elements.push(copyProcessInstanceShortLinkButton());
    if (ability.can('POST', `${targetUris.processInstanceTerminatePath}`)) {
      elements.push(terminateButton());
    }
    if (ability.can('POST', `${targetUris.processInstanceSuspendPath}`)) {
      elements.push(suspendButton());
    }
    if (ability.can('POST', `${targetUris.processInstanceResumePath}`)) {
      elements.push(resumeButton());
    }
    if (ability.can('DELETE', targetUris.processInstanceActionPath)) {
      elements.push(deleteButton());
    }
    let toast = null;
    if (copiedShortLinkToClipboard) {
      toast = (
        <Notification
          onClose={() => setCopiedShortLinkToClipboard(false)}
          type="success"
          title="Copied link to clipboard"
          timeout={3000}
          hideCloseButton
          withBottomMargin={false}
        />
      );
      elements.push(toast);
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

  const diagramArea = (processModelId: string) => {
    if (!processInstance) {
      return null;
    }

    const detailsComponent = (
      <>
        {childrenForErrorObject(
          errorForDisplayFromString(
            processInstance.bpmn_xml_file_contents_retrieval_error || ''
          )
        )}
      </>
    );
    return processInstance.bpmn_xml_file_contents_retrieval_error ? (
      <Notification
        title="Failed to load diagram"
        type="error"
        hideCloseButton
        allowTogglingFullMessage
      >
        {detailsComponent}
      </Notification>
    ) : (
      <>
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
  };

  const updateSelectedTab = (newTabIndex: any) => {
    // this causes the process instance and task list to render again as well
    // it'd be nice if we could find a way to avoid that
    updateSearchParams(newTabIndex.selectedIndex, 'tab');
  };

  const updateSelectedTaskTabSubTab = (newTabIndex: any) => {
    updateSearchParams(newTabIndex.selectedIndex, 'taskSubTab');
  };

  const taskTabSubTabs = () => {
    if (!processInstance) {
      return null;
    }

    return (
      <Tabs
        selectedIndex={selectedTaskTabSubTab}
        onChange={updateSelectedTaskTabSubTab}
      >
        <TabList aria-label="List of tabs">
          <Tab>Completed by me</Tab>
          <Tab>All completed</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            {selectedTaskTabSubTab === 0 ? (
              <TaskListTable
                apiPath={`/tasks/completed-by-me/${processInstance.id}`}
                paginationClassName="with-large-bottom-margin"
                textToShowIfEmpty="You have not completed any tasks for this process instance."
                shouldPaginateTable={false}
                showProcessModelIdentifier={false}
                showProcessId={false}
                showStartedBy={false}
                showTableDescriptionAsTooltip
                showDateStarted={false}
                showWaitingOn={false}
                canCompleteAllTasks={false}
                showViewFormDataButton
                defaultPerPage={20}
              />
            ) : null}
          </TabPanel>
          <TabPanel>
            {selectedTaskTabSubTab === 1 ? (
              <TaskListTable
                apiPath={`/tasks/completed/${processInstance.id}`}
                paginationClassName="with-large-bottom-margin"
                textToShowIfEmpty="There are no completed tasks for this process instance."
                shouldPaginateTable={false}
                showProcessModelIdentifier={false}
                showProcessId={false}
                showStartedBy={false}
                showTableDescriptionAsTooltip
                showDateStarted={false}
                showWaitingOn={false}
                canCompleteAllTasks={false}
                showCompletedBy
                showActionsColumn={false}
                defaultPerPage={20}
              />
            ) : null}
          </TabPanel>
        </TabPanels>
      </Tabs>
    );
  };

  if (processInstance && (tasks || tasksCallHadError) && permissionsLoaded) {
    const processModelId = unModifyProcessIdentifierForPathParam(
      params.process_model_id ? params.process_model_id : ''
    );

    // eslint-disable-next-line sonarjs/cognitive-complexity
    const getTabs = () => {
      const canViewLogs = ability.can(
        'GET',
        targetUris.processInstanceLogListPath
      );
      const canViewMsgs = ability.can(
        'GET',
        targetUris.messageInstanceListPath
      );

      const getMessageDisplay = () => {
        if (canViewMsgs) {
          return <MessageInstanceList processInstanceId={processInstance.id} />;
        }
        return null;
      };

      return (
        <Tabs selectedIndex={selectedTabIndex} onChange={updateSelectedTab}>
          <TabList aria-label="List of tabs">
            <Tab>Diagram</Tab>
            <Tab disabled={!canViewLogs}>Milestones</Tab>
            <Tab disabled={!canViewLogs}>Events</Tab>
            <Tab disabled={!canViewMsgs}>Messages</Tab>
            <Tab>Tasks</Tab>
          </TabList>
          <TabPanels>
            <TabPanel>
              {selectedTabIndex === 0 ? (
                <TabPanel>{diagramArea(processModelId)}</TabPanel>
              ) : null}
            </TabPanel>
            <TabPanel>
              {selectedTabIndex === 1 ? (
                <ProcessInstanceLogList
                  variant={variant}
                  isEventsView={false}
                  processModelId={modifiedProcessModelId || ''}
                  processInstanceId={processInstance.id}
                />
              ) : null}
            </TabPanel>
            <TabPanel>
              {selectedTabIndex === 2 ? (
                <ProcessInstanceLogList
                  variant={variant}
                  isEventsView
                  processModelId={modifiedProcessModelId || ''}
                  processInstanceId={processInstance.id}
                />
              ) : null}
            </TabPanel>
            <TabPanel>
              {selectedTabIndex === 3 ? getMessageDisplay() : null}
            </TabPanel>
            <TabPanel>
              {selectedTabIndex === 4 ? taskTabSubTabs() : null}
            </TabPanel>
          </TabPanels>
        </Tabs>
      );
    };

    return (
      <>
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: processModelId,
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [`Process Instance Id: ${processInstance.id}`],
          ]}
        />
        {keyboardShortcutArea}
        {taskUpdateDisplayArea()}
        {processDataDisplayArea()}
        {viewMostRecentStateComponent()}
        <Stack orientation="horizontal" gap={1}>
          <h1 className="with-icons">
            Process Instance Id: {processInstance.id}
          </h1>
          {buttonIcons()}
        </Stack>
        {getInfoTag()}
        <br />
        <ProcessInstanceCurrentTaskInfo processInstance={processInstance} />
        <br />
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
        {getTabs()}
      </>
    );
  }
  return null;
}

import { useContext, useEffect, useState } from 'react';
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
  CaretLeft,
  CaretRight,
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
  // @ts-ignore
} from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ReactDiagramEditor from '../components/ReactDiagramEditor';
import {
  convertSecondsToFormattedDateTime,
  unModifyProcessIdentifierForPathParam,
} from '../helpers';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import ErrorContext from '../contexts/ErrorContext';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  PermissionsToCheck,
  ProcessData,
  ProcessInstance,
  ProcessInstanceTask,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessInstanceClass from '../classes/ProcessInstanceClass';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceShow({ variant }: OwnProps) {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [tasksCallHadError, setTasksCallHadError] = useState<boolean>(false);
  const [taskToDisplay, setTaskToDisplay] = useState<object | null>(null);
  const [taskDataToDisplay, setTaskDataToDisplay] = useState<string>('');
  const [processDataToDisplay, setProcessDataToDisplay] =
    useState<ProcessData | null>(null);
  const [editingTaskData, setEditingTaskData] = useState<boolean>(false);
  const [selectingEvent, setSelectingEvent] = useState<boolean>(false);
  const [eventToSend, setEventToSend] = useState<any>({});
  const [eventPayload, setEventPayload] = useState<string>('{}');
  const [eventTextEditorEnabled, setEventTextEditorEnabled] =
    useState<boolean>(false);

  const setErrorObject = (useContext as any)(ErrorContext)[1];

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
    [targetUris.processInstanceTaskListDataPath]: ['GET', 'PUT'],
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

  useEffect(() => {
    if (permissionsLoaded) {
      const processTaskFailure = () => {
        setTasksCallHadError(true);
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
      let taskParams = '?all_tasks=true';
      if (typeof params.spiff_step !== 'undefined') {
        taskParams = `${taskParams}&spiff_step=${params.spiff_step}`;
      }
      let taskPath = '';
      if (ability.can('GET', targetUris.processInstanceTaskListDataPath)) {
        taskPath = `${targetUris.processInstanceTaskListDataPath}${taskParams}`;
      } else if (ability.can('GET', taskListPath)) {
        taskPath = `${taskListPath}${taskParams}`;
      }
      if (taskPath) {
        HttpService.makeCallToBackend({
          path: taskPath,
          successCallback: setTasks,
          failureCallback: processTaskFailure,
        });
      } else {
        setTasksCallHadError(true);
      }
    }
  }, [
    params,
    modifiedProcessModelId,
    permissionsLoaded,
    ability,
    targetUris,
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

  const getTaskIds = () => {
    const taskIds = { completed: [], readyOrWaiting: [] };
    if (tasks) {
      tasks.forEach(function getUserTasksElement(task: ProcessInstanceTask) {
        const callingSubprocessId = searchParams.get('call_activity_task_id');
        if (
          !callingSubprocessId ||
          callingSubprocessId === task.calling_subprocess_task_id
        ) {
          console.log('callingSubprocessId', callingSubprocessId);
          if (task.state === 'COMPLETED') {
            (taskIds.completed as any).push(task);
          }
          if (task.state === 'READY' || task.state === 'WAITING') {
            (taskIds.readyOrWaiting as any).push(task);
          }
        }
      });
    }
    return taskIds;
  };

  const currentSpiffStep = () => {
    if (processInstance && typeof params.spiff_step === 'undefined') {
      return processInstance.spiff_step || 0;
    }

    return Number(params.spiff_step);
  };

  const showingFirstSpiffStep = () => {
    return currentSpiffStep() === 1;
  };

  const showingLastSpiffStep = () => {
    return processInstance && currentSpiffStep() === processInstance.spiff_step;
  };

  const spiffStepLink = (label: any, distance: number) => {
    const processIdentifier = searchParams.get('process_identifier');
    let queryParams = '';
    if (processIdentifier) {
      queryParams = `?process_identifier=${processIdentifier}`;
    }
    return (
      <Link
        reloadDocument
        data-qa="process-instance-step-link"
        to={`/admin/process-instances/${params.process_model_id}/${
          params.process_instance_id
        }/${currentSpiffStep() + distance}${queryParams}`}
      >
        {label}
      </Link>
    );
  };

  const previousStepLink = () => {
    if (showingFirstSpiffStep()) {
      return null;
    }

    return spiffStepLink(<CaretLeft />, -1);
  };

  const nextStepLink = () => {
    if (showingLastSpiffStep()) {
      return null;
    }

    return spiffStepLink(<CaretRight />, 1);
  };

  const returnToLastSpiffStep = () => {
    window.location.href = `/admin/process-instances/${params.process_model_id}/${params.process_instance_id}`;
  };

  const resetProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceResetPath}/${currentSpiffStep()}`,
      successCallback: returnToLastSpiffStep,
      httpMethod: 'POST',
    });
  };

  const getInfoTag = () => {
    if (!processInstance) {
      return null;
    }
    const currentEndDate = convertSecondsToFormattedDateTime(
      processInstance.end_in_seconds || 0
    );
    let currentEndDateTag;
    if (currentEndDate) {
      currentEndDateTag = (
        <Grid condensed fullWidth>
          <Column sm={1} md={1} lg={2} className="grid-list-title">
            Completed:{' '}
          </Column>
          <Column sm={3} md={3} lg={3} className="grid-date">
            {convertSecondsToFormattedDateTime(
              processInstance.end_in_seconds || 0
            ) || 'N/A'}
          </Column>
        </Grid>
      );
    }

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
            Started:{' '}
          </Column>
          <Column sm={3} md={3} lg={3} className="grid-date">
            {convertSecondsToFormattedDateTime(
              processInstance.start_in_seconds || 0
            )}
          </Column>
        </Grid>
        {currentEndDateTag}
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
                  href={`/admin/logs/${modifiedProcessModelId}/${params.process_instance_id}`}
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

  const initializeTaskDataToDisplay = (task: any) => {
    if (task == null) {
      setTaskDataToDisplay('');
    } else {
      setTaskDataToDisplay(JSON.stringify(task.data, null, 2));
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
      const matchingTask: any = tasks.find((task: any) => {
        const callingSubprocessId = searchParams.get('call_activity_task_id');
        return (
          (!callingSubprocessId ||
            callingSubprocessId === task.calling_subprocess_task_id) &&
          task.name === shapeElement.id &&
          bpmnProcessIdentifiers.includes(task.process_identifier)
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
      return tasks.find((task: any) => task.id === taskId);
    }
    return null;
  };

  const processScriptUnitTestCreateResult = (result: any) => {
    console.log('result', result);
  };

  const createScriptUnitTest = () => {
    if (taskToDisplay) {
      const taskToUse: any = taskToDisplay;
      const previousTask: any = getTaskById(taskToUse.parent);
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/script-unit-tests`,
        httpMethod: 'POST',
        successCallback: processScriptUnitTestCreateResult,
        postBody: {
          bpmn_task_identifier: taskToUse.name,
          input_json: previousTask.data,
          expected_output_json: taskToUse.data,
        },
      });
    }
  };

  const canEditTaskData = (task: any) => {
    return (
      processInstance &&
      ability.can('PUT', targetUris.processInstanceTaskListDataPath) &&
      task.state === 'READY' &&
      processInstance.status === 'suspended' &&
      showingLastSpiffStep()
    );
  };

  const canSendEvent = (task: any) => {
    // We actually could allow this for any waiting events
    const taskTypes = ['Event Based Gateway'];
    return (
      processInstance &&
      processInstance.status === 'waiting' &&
      ability.can('POST', targetUris.processInstanceSendEventPath) &&
      taskTypes.filter((t) => t === task.type).length > 0 &&
      task.state === 'WAITING' &&
      showingLastSpiffStep()
    );
  };

  const canCompleteTask = (task: any) => {
    return (
      processInstance &&
      processInstance.status === 'suspended' &&
      ability.can('POST', targetUris.processInstanceCompleteTaskPath) &&
      task.state === 'READY' &&
      showingLastSpiffStep()
    );
  };

  const canResetProcess = (task: any) => {
    return (
      ability.can('POST', targetUris.processInstanceResetPath) &&
      processInstance &&
      processInstance.status === 'suspended' &&
      task.state === 'READY' &&
      !showingLastSpiffStep()
    );
  };

  const getEvents = (task: any) => {
    const handleMessage = (eventDefinition: any) => {
      if (eventDefinition.typename === 'MessageEventDefinition') {
        const newEvent = eventDefinition;
        delete newEvent.message_var;
        newEvent.payload = {};
        return newEvent;
      }
      return eventDefinition;
    };
    if (task.event_definition && task.event_definition.event_definitions)
      return task.event_definition.event_definitions.map((e: any) =>
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
    setErrorObject(null);
  };

  const taskDataStringToObject = (dataString: string) => {
    return JSON.parse(dataString);
  };

  const saveTaskDataResult = (_: any) => {
    setEditingTaskData(false);
    const dataObject = taskDataStringToObject(taskDataToDisplay);
    const taskToDisplayCopy = { ...taskToDisplay, data: dataObject }; // spread operator
    setTaskToDisplay(taskToDisplayCopy);
    refreshPage();
  };

  const saveTaskDataFailure = (result: any) => {
    setErrorObject({ message: result.message });
  };

  const saveTaskData = () => {
    if (!taskToDisplay) {
      return;
    }

    setErrorObject(null);

    // taskToUse is copy of taskToDisplay, with taskDataToDisplay in data attribute
    const taskToUse: any = { ...taskToDisplay, data: taskDataToDisplay };
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceTaskListDataPath}/${taskToUse.id}`,
      httpMethod: 'PUT',
      successCallback: saveTaskDataResult,
      failureCallback: saveTaskDataFailure,
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
      failureCallback: saveTaskDataFailure,
      postBody: eventToSend,
    });
  };

  const completeTask = (execute: boolean) => {
    const taskToUse: any = taskToDisplay;
    HttpService.makeCallToBackend({
      path: `/task-complete/${modifiedProcessModelId}/${params.process_instance_id}/${taskToUse.id}`,
      httpMethod: 'POST',
      successCallback: returnToLastSpiffStep,
      postBody: { execute },
    });
  };

  const taskDisplayButtons = (task: any) => {
    const buttons = [];

    if (
      task.type === 'Script Task' &&
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

    if (task.type === 'Call Activity') {
      buttons.push(
        <Link
          data-qa="go-to-call-activity-result"
          to={`${window.location.pathname}?process_identifier=${task.call_activity_process_identifier}&call_activity_task_id=${task.id}`}
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
        buttons.push(
          <Button
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
    return editingTaskData ? (
      <Editor
        height={600}
        width="auto"
        defaultLanguage="json"
        defaultValue={taskDataToDisplay}
        onChange={(value) => setTaskDataToDisplay(value || '')}
      />
    ) : (
      <pre>{taskDataToDisplay}</pre>
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

  const taskUpdateDisplayArea = () => {
    const taskToUse: any = { ...taskToDisplay, data: taskDataToDisplay };
    const candidateEvents: any = getEvents(taskToUse);
    if (taskToDisplay) {
      return (
        <Modal
          open={!!taskToUse}
          passiveModal
          onRequestClose={handleTaskDataDisplayClose}
        >
          <Stack orientation="horizontal" gap={2}>
            {taskToUse.name} ({taskToUse.type}): {taskToUse.state}
            {taskDisplayButtons(taskToUse)}
          </Stack>
          {selectingEvent
            ? eventSelector(candidateEvents)
            : taskDataContainer()}
        </Modal>
      );
    }
    return null;
  };

  const stepsElement = () => {
    if (!processInstance) {
      return null;
    }
    return (
      <Grid condensed fullWidth>
        <Column sm={3} md={3} lg={3}>
          <Stack orientation="horizontal" gap={3} className="smaller-text">
            {previousStepLink()}
            Step {currentSpiffStep()} of {processInstance.spiff_step}
            {nextStepLink()}
          </Stack>
        </Column>
      </Grid>
    );
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

  if (processInstance && (tasks || tasksCallHadError)) {
    const taskIds = getTaskIds();
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
        {getInfoTag()}
        <br />
        {taskUpdateDisplayArea()}
        {processDataDisplayArea()}
        {stepsElement()}
        <br />
        <ReactDiagramEditor
          processModelId={processModelId || ''}
          diagramXML={processInstance.bpmn_xml_file_contents || ''}
          fileName={processInstance.bpmn_xml_file_contents || ''}
          readyOrWaitingProcessInstanceTasks={taskIds.readyOrWaiting}
          completedProcessInstanceTasks={taskIds.completed}
          diagramType="readonly"
          onElementClick={handleClickedDiagramTask}
        />

        <div id="diagram-container" />
      </>
    );
  }
  return null;
}

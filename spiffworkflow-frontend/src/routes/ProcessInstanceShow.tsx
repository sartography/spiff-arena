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
  ProcessInstance,
  ProcessInstanceTask,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';

export default function ProcessInstanceShow() {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams] = useSearchParams();

  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);
  const [tasks, setTasks] = useState<ProcessInstanceTask[] | null>(null);
  const [tasksCallHadError, setTasksCallHadError] = useState<boolean>(false);
  const [taskToDisplay, setTaskToDisplay] = useState<object | null>(null);
  const [taskDataToDisplay, setTaskDataToDisplay] = useState<string>('');
  const [editingTaskData, setEditingTaskData] = useState<boolean>(false);

  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const unModifiedProcessModelId = unModifyProcessIdentifierForPathParam(
    `${params.process_model_id}`
  );
  const modifiedProcessModelId = params.process_model_id;

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.messageInstanceListPath]: ['GET'],
    [targetUris.processInstanceTaskListPath]: ['GET'],
    [targetUris.processInstanceTaskListDataPath]: ['GET', 'PUT'],
    [targetUris.processInstanceActionPath]: ['DELETE'],
    [targetUris.processInstanceLogListPath]: ['GET'],
    [targetUris.processModelShowPath]: ['PUT'],
    [`${targetUris.processInstanceActionPath}/suspend`]: ['PUT'],
    [`${targetUris.processInstanceActionPath}/terminate`]: ['PUT'],
    [`${targetUris.processInstanceActionPath}/resume`]: ['PUT'],
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
      HttpService.makeCallToBackend({
        path: `/process-instances/${modifiedProcessModelId}/${params.process_instance_id}${queryParams}`,
        successCallback: setProcessInstance,
      });
      let taskParams = '?all_tasks=true';
      if (typeof params.spiff_step !== 'undefined') {
        taskParams = `${taskParams}&spiff_step=${params.spiff_step}`;
      }
      let taskPath = '';
      if (ability.can('GET', targetUris.processInstanceTaskListDataPath)) {
        taskPath = `${targetUris.processInstanceTaskListDataPath}${taskParams}`;
      } else if (ability.can('GET', targetUris.processInstanceTaskListPath)) {
        taskPath = `${targetUris.processInstanceTaskListPath}${taskParams}`;
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
      path: `${targetUris.processInstanceActionPath}/terminate`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const suspendProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceActionPath}/suspend`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const resumeProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceActionPath}/resume`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const getTaskIds = () => {
    const taskIds = { completed: [], readyOrWaiting: [] };
    if (tasks) {
      tasks.forEach(function getUserTasksElement(task: ProcessInstanceTask) {
        if (task.state === 'COMPLETED') {
          (taskIds.completed as any).push(task);
        }
        if (task.state === 'READY' || task.state === 'WAITING') {
          (taskIds.readyOrWaiting as any).push(task);
        }
      });
    }
    return taskIds;
  };

  const currentSpiffStep = (processInstanceToUse: any) => {
    if (typeof params.spiff_step === 'undefined') {
      return processInstanceToUse.spiff_step;
    }

    return Number(params.spiff_step);
  };

  const showingFirstSpiffStep = (processInstanceToUse: any) => {
    return currentSpiffStep(processInstanceToUse) === 1;
  };

  const showingLastSpiffStep = (processInstanceToUse: any) => {
    return (
      currentSpiffStep(processInstanceToUse) === processInstanceToUse.spiff_step
    );
  };

  const spiffStepLink = (
    processInstanceToUse: any,
    label: any,
    distance: number
  ) => {
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
        }/${currentSpiffStep(processInstanceToUse) + distance}${queryParams}`}
      >
        {label}
      </Link>
    );
  };

  const previousStepLink = (processInstanceToUse: any) => {
    if (showingFirstSpiffStep(processInstanceToUse)) {
      return null;
    }

    return spiffStepLink(processInstanceToUse, <CaretLeft />, -1);
  };

  const nextStepLink = (processInstanceToUse: any) => {
    if (showingLastSpiffStep(processInstanceToUse)) {
      return null;
    }

    return spiffStepLink(processInstanceToUse, <CaretRight />, 1);
  };

  const getInfoTag = (processInstanceToUse: any) => {
    const currentEndDate = convertSecondsToFormattedDateTime(
      processInstanceToUse.end_in_seconds
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
              processInstanceToUse.end_in_seconds
            ) || 'N/A'}
          </Column>
        </Grid>
      );
    }

    let statusIcon = <InProgress />;
    if (processInstanceToUse.status === 'suspended') {
      statusIcon = <PauseOutline />;
    } else if (processInstanceToUse.status === 'complete') {
      statusIcon = <Checkmark />;
    } else if (processInstanceToUse.status === 'terminated') {
      statusIcon = <StopOutline />;
    } else if (processInstanceToUse.status === 'error') {
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
              processInstanceToUse.start_in_seconds
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
              {processInstanceToUse.status} {statusIcon}
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

  const terminateButton = (processInstanceToUse: any) => {
    if (
      ['complete', 'terminated', 'error'].indexOf(
        processInstanceToUse.status
      ) === -1
    ) {
      return (
        <ButtonWithConfirmation
          kind="ghost"
          renderIcon={StopOutline}
          iconDescription="Terminate"
          hasIconOnly
          description={`Terminate Process Instance: ${processInstanceToUse.id}`}
          onConfirmation={terminateProcessInstance}
          confirmButtonLabel="Terminate"
        />
      );
    }
    return <div />;
  };

  const suspendButton = (processInstanceToUse: any) => {
    if (
      ['complete', 'terminated', 'error', 'suspended'].indexOf(
        processInstanceToUse.status
      ) === -1
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

  const resumeButton = (processInstanceToUse: any) => {
    if (processInstanceToUse.status === 'suspended') {
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

  const handleClickedDiagramTask = (
    shapeElement: any,
    bpmnProcessIdentifiers: any
  ) => {
    if (tasks) {
      const matchingTask: any = tasks.find(
        (task: any) =>
          task.name === shapeElement.id &&
          bpmnProcessIdentifiers.includes(task.process_identifier)
      );
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
      ability.can('PUT', targetUris.processInstanceTaskListDataPath) &&
      task.state === 'READY' &&
      showingLastSpiffStep(processInstance as any)
    );
  };

  const cancelEditingTaskData = () => {
    setEditingTaskData(false);
    initializeTaskDataToDisplay(taskToDisplay);
    setErrorMessage(null);
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
    setErrorMessage({ message: result.toString() });
  };

  const saveTaskData = () => {
    if (!taskToDisplay) {
      return;
    }

    setErrorMessage(null);

    // taskToUse is copy of taskToDisplay, with taskDataToDisplay in data attribute
    const taskToUse: any = { ...taskToDisplay, data: taskDataToDisplay };
    HttpService.makeCallToBackend({
      path: `/task-data/${modifiedProcessModelId}/${params.process_instance_id}/${taskToUse.id}`,
      httpMethod: 'PUT',
      successCallback: saveTaskDataResult,
      failureCallback: saveTaskDataFailure,
      postBody: {
        new_task_data: taskToUse.data,
      },
    });
  };

  const taskDataButtons = (task: any) => {
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
          to={`${window.location.pathname}?process_identifier=${task.call_activity_process_identifier}`}
          target="_blank"
        >
          View Call Activity Diagram
        </Link>
      );
    }

    if (canEditTaskData(task)) {
      if (editingTaskData) {
        buttons.push(
          <Button data-qa="save-task-data-button" onClick={saveTaskData}>
            Save
          </Button>
        );
        buttons.push(
          <Button
            data-qa="cancel-task-data-edit-button"
            onClick={cancelEditingTaskData}
          >
            Cancel
          </Button>
        );
      } else {
        buttons.push(
          <Button
            data-qa="edit-task-data-button"
            onClick={() => setEditingTaskData(true)}
          >
            Edit
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

  const taskDataDisplayArea = () => {
    const taskToUse: any = { ...taskToDisplay, data: taskDataToDisplay };
    if (taskToDisplay) {
      return (
        <Modal
          open={!!taskToUse}
          passiveModal
          onRequestClose={handleTaskDataDisplayClose}
        >
          <Stack orientation="horizontal" gap={2}>
            {taskToUse.name} ({taskToUse.type}): {taskToUse.state}
            {taskDataButtons(taskToUse)}
          </Stack>
          {taskDataContainer()}
        </Modal>
      );
    }
    return null;
  };

  const stepsElement = (processInstanceToUse: any) => {
    return (
      <Grid condensed fullWidth>
        <Column sm={3} md={3} lg={3}>
          <Stack orientation="horizontal" gap={3} className="smaller-text">
            {previousStepLink(processInstanceToUse)}
            Step {currentSpiffStep(processInstanceToUse)} of{' '}
            {processInstanceToUse.spiff_step}
            {nextStepLink(processInstanceToUse)}
          </Stack>
        </Column>
      </Grid>
    );
  };

  const buttonIcons = (processInstanceToUse: any) => {
    const elements = [];
    if (
      ability.can('POST', `${targetUris.processInstanceActionPath}/terminate`)
    ) {
      elements.push(terminateButton(processInstanceToUse));
    }
    if (
      ability.can('POST', `${targetUris.processInstanceActionPath}/suspend`)
    ) {
      elements.push(suspendButton(processInstanceToUse));
    }
    if (ability.can('POST', `${targetUris.processInstanceActionPath}/resume`)) {
      elements.push(resumeButton(processInstanceToUse));
    }
    if (ability.can('DELETE', targetUris.processInstanceActionPath)) {
      elements.push(
        <ButtonWithConfirmation
          data-qa="process-instance-delete"
          kind="ghost"
          renderIcon={TrashCan}
          iconDescription="Delete"
          hasIconOnly
          description={`Delete Process Instance: ${processInstanceToUse.id}`}
          onConfirmation={deleteProcessInstance}
          confirmButtonLabel="Delete"
        />
      );
    }
    return elements;
  };

  if (processInstance && (tasks || tasksCallHadError)) {
    const processInstanceToUse = processInstance as any;
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
            [`Process Instance Id: ${processInstanceToUse.id}`],
          ]}
        />
        <Stack orientation="horizontal" gap={1}>
          <h1 className="with-icons">
            Process Instance Id: {processInstanceToUse.id}
          </h1>
          {buttonIcons(processInstanceToUse)}
        </Stack>
        <br />
        <br />
        {getInfoTag(processInstanceToUse)}
        <br />
        {taskDataDisplayArea()}
        {stepsElement(processInstanceToUse)}
        <br />
        <ReactDiagramEditor
          processModelId={processModelId || ''}
          diagramXML={processInstanceToUse.bpmn_xml_file_contents || ''}
          fileName={processInstanceToUse.bpmn_xml_file_contents || ''}
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

import { useContext, useEffect, useState } from 'react';
import Editor from '@monaco-editor/react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button, Modal, Stack } from 'react-bootstrap';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import ReactDiagramEditor from '../components/ReactDiagramEditor';
import { convertSecondsToFormattedDate } from '../helpers';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import ErrorContext from '../contexts/ErrorContext';

export default function ProcessInstanceShow() {
  const navigate = useNavigate();
  const params = useParams();

  const [processInstance, setProcessInstance] = useState(null);
  const [tasks, setTasks] = useState<Array<object> | null>(null);
  const [taskToDisplay, setTaskToDisplay] = useState<object | null>(null);
  const [taskDataToDisplay, setTaskDataToDisplay] = useState<string>('');
  const [editingTaskData, setEditingTaskData] = useState<boolean>(false);

  const setErrorMessage = (useContext as any)(ErrorContext)[1];

  const navigateToProcessInstances = (_result: any) => {
    navigate(
      `/admin/process-instances?process_group_identifier=${params.process_group_id}&process_model_identifier=${params.process_model_id}`
    );
  };

  useEffect(() => {
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/${params.process_instance_id}`,
      successCallback: setProcessInstance,
    });
    if (typeof params.spiff_step === 'undefined')
      HttpService.makeCallToBackend({
        path: `/process-instance/${params.process_instance_id}/tasks?all_tasks=true`,
        successCallback: setTasks,
      });
    else
      HttpService.makeCallToBackend({
        path: `/process-instance/${params.process_instance_id}/tasks?all_tasks=true&spiff_step=${params.spiff_step}`,
        successCallback: setTasks,
      });
  }, [params]);

  const deleteProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/${params.process_instance_id}`,
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
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/${params.process_instance_id}/terminate`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const suspendProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/${params.process_instance_id}/suspend`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const resumeProcessInstance = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/${params.process_instance_id}/resume`,
      successCallback: refreshPage,
      httpMethod: 'POST',
    });
  };

  const getTaskIds = () => {
    const taskIds = { completed: [], readyOrWaiting: [] };
    if (tasks) {
      tasks.forEach(function getUserTasksElement(task: any) {
        if (task.state === 'COMPLETED') {
          (taskIds.completed as any).push(task.name);
        }
        if (task.state === 'READY' || task.state === 'WAITING') {
          (taskIds.readyOrWaiting as any).push(task.name);
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
    label: string,
    distance: number
  ) => {
    return (
      <li>
        <Link
          data-qa="process-instance-prev-step-link"
          to={`/admin/process-models/${params.process_group_id}/${
            params.process_model_id
          }/process-instances/${params.process_instance_id}/${
            currentSpiffStep(processInstanceToUse) + distance
          }`}
        >
          {label}
        </Link>
      </li>
    );
  };

  const previousStepLink = (processInstanceToUse: any) => {
    if (showingFirstSpiffStep(processInstanceToUse)) {
      return null;
    }

    return spiffStepLink(processInstanceToUse, 'Previous Step', -1);
  };

  const nextStepLink = (processInstanceToUse: any) => {
    if (showingLastSpiffStep(processInstanceToUse)) {
      return null;
    }

    return spiffStepLink(processInstanceToUse, 'Next Step', 1);
  };

  const getInfoTag = (processInstanceToUse: any) => {
    const currentEndDate = convertSecondsToFormattedDate(
      processInstanceToUse.end_in_seconds
    );
    let currentEndDateTag;
    if (currentEndDate) {
      currentEndDateTag = (
        <li>
          Completed:{' '}
          {convertSecondsToFormattedDate(processInstanceToUse.end_in_seconds) ||
            'N/A'}
        </li>
      );
    }

    return (
      <ul>
        <li>
          Started:{' '}
          {convertSecondsToFormattedDate(processInstanceToUse.start_in_seconds)}
        </li>
        {currentEndDateTag}
        <li>Status: {processInstanceToUse.status}</li>
        <li>
          <Link
            data-qa="process-instance-log-list-link"
            to={`/admin/process-models/${params.process_group_id}/${params.process_model_id}/process-instances/${params.process_instance_id}/logs`}
          >
            Logs
          </Link>
        </li>
        <li>
          <Link
            data-qa="process-instance-message-instance-list-link"
            to={`/admin/messages?process_group_id=${params.process_group_id}&process_model_id=${params.process_model_id}&process_instance_id=${params.process_instance_id}`}
          >
            Messages
          </Link>
        </li>
        <li>
          Step {currentSpiffStep(processInstanceToUse)} of{' '}
          {processInstanceToUse.spiff_step}
        </li>
        {previousStepLink(processInstanceToUse)}
        {nextStepLink(processInstanceToUse)}
      </ul>
    );
  };

  const terminateButton = (processInstanceToUse: any) => {
    if (
      ['complete', 'terminated', 'faulted'].indexOf(
        processInstanceToUse.status
      ) === -1
    ) {
      return (
        <Button onClick={terminateProcessInstance} variant="warning">
          Terminate
        </Button>
      );
    }
    return <div />;
  };

  const suspendButton = (processInstanceToUse: any) => {
    if (
      ['complete', 'terminated', 'faulted', 'suspended'].indexOf(
        processInstanceToUse.status
      ) === -1
    ) {
      return (
        <Button onClick={suspendProcessInstance} variant="warning">
          Suspend
        </Button>
      );
    }
    return <div />;
  };

  const resumeButton = (processInstanceToUse: any) => {
    if (processInstanceToUse.status === 'suspended') {
      return (
        <Button onClick={resumeProcessInstance} variant="warning">
          Resume
        </Button>
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

  const handleClickedDiagramTask = (shapeElement: any) => {
    if (tasks) {
      const matchingTask: any = tasks.find(
        (task: any) => task.name === shapeElement.id
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
        path: `/process-models/${params.process_group_id}/${params.process_model_id}/script-unit-tests`,
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
      task.state === 'READY' && showingLastSpiffStep(processInstance as any)
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
      path: `/process-instances/${params.process_instance_id}/task/${taskToUse.id}/update`,
      httpMethod: 'POST',
      successCallback: saveTaskDataResult,
      failureCallback: saveTaskDataFailure,
      postBody: {
        new_task_data: taskToUse.data,
      },
    });
  };

  const taskDataButtons = (task: any) => {
    const buttons = [];

    if (task.type === 'Script Task') {
      buttons.push(
        <Button
          data-qa="create-script-unit-test-button"
          onClick={createScriptUnitTest}
        >
          Create Script Unit Test
        </Button>
      );
    }

    if (canEditTaskData(task)) {
      if (editingTaskData) {
        buttons.push(
          <Button
            data-qa="create-script-unit-test-button"
            onClick={saveTaskData}
          >
            Save
          </Button>
        );
        buttons.push(
          <Button
            data-qa="create-script-unit-test-button"
            onClick={cancelEditingTaskData}
          >
            Cancel
          </Button>
        );
      } else {
        buttons.push(
          <Button
            data-qa="create-script-unit-test-button"
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
        <Modal show={!!taskToUse} onHide={handleTaskDataDisplayClose}>
          <Modal.Header closeButton>
            <Modal.Title>
              <Stack direction="horizontal" gap={2}>
                {taskToUse.name} ({taskToUse.type}): {taskToUse.state}
                {taskDataButtons(taskToUse)}
              </Stack>
            </Modal.Title>
          </Modal.Header>
          {taskDataContainer()}
        </Modal>
      );
    }
    return null;
  };

  if (processInstance && tasks) {
    const processInstanceToUse = processInstance as any;
    const taskIds = getTaskIds();

    return (
      <>
        <ProcessBreadcrumb
          processModelId={params.process_model_id}
          processGroupId={params.process_group_id}
          linkProcessModel
        />
        <Stack direction="horizontal" gap={3}>
          <h2>Process Instance Id: {processInstanceToUse.id}</h2>
          <ButtonWithConfirmation
            description="Delete Process Instance?"
            onConfirmation={deleteProcessInstance}
            buttonLabel="Delete"
          />
          {terminateButton(processInstanceToUse)}
          {suspendButton(processInstanceToUse)}
          {resumeButton(processInstanceToUse)}
        </Stack>
        {getInfoTag(processInstanceToUse)}
        {taskDataDisplayArea()}
        <ReactDiagramEditor
          processModelId={params.process_model_id || ''}
          processGroupId={params.process_group_id || ''}
          diagramXML={processInstanceToUse.bpmn_xml_file_contents || ''}
          fileName={processInstanceToUse.bpmn_xml_file_contents || ''}
          readyOrWaitingBpmnTaskIds={taskIds.readyOrWaiting}
          completedTasksBpmnIds={taskIds.completed}
          diagramType="readonly"
          onElementClick={handleClickedDiagramTask}
        />

        <div id="diagram-container" />
      </>
    );
  }
  return null;
}

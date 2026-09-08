import { useCallback, useState } from 'react';
import type { AppAbility } from '../../contexts/Can';
import type { useUriListForPermissions } from '../../hooks/UriListForPermissions';
import useAPIError from '../../hooks/UseApiError';
import HttpService from '../../services/HttpService';
import { HUMAN_TASK_TYPES } from '../../helpers';
import {
  BasicTask,
  ErrorForDisplay,
  EventDefinition,
  ProcessInstance,
  Task,
  User,
} from '../../interfaces';
import type { TaskInspectorDialogProps } from './TaskInspectorDialog';

export const EVENTS_THAT_NEED_PAYLOAD = ['MessageEventDefinition'];

type UseTaskInspectorOptions = {
  processInstanceId?: string;
  modifiedProcessModelId?: string;
  tasks: BasicTask[] | null;
  processInstance: ProcessInstance | null;
  showingActiveTask: boolean;
  ability: AppAbility;
  targetUris: ReturnType<typeof useUriListForPermissions>['targetUris'];
  completionViewBaseUrl: string;
  completionQueryParams: string;
  onSendEventSuccess: () => void;
  onCompleteTaskSuccess: () => void;
  onResetProcess: (taskGuid: string) => void;
  onNavigateCallActivity: (task: BasicTask, event: any) => void;
};

export default function useTaskInspector({
  processInstanceId,
  modifiedProcessModelId,
  tasks,
  processInstance,
  showingActiveTask,
  ability,
  targetUris,
  completionViewBaseUrl,
  completionQueryParams,
  onSendEventSuccess,
  onCompleteTaskSuccess,
  onResetProcess,
  onNavigateCallActivity,
}: UseTaskInspectorOptions): {
  openTaskInspector: (task: BasicTask) => void;
  dialogProps: TaskInspectorDialogProps;
} {
  const [taskToDisplay, setTaskToDisplay] = useState<BasicTask | null>(null);
  const [taskDataToDisplay, setTaskDataToDisplay] = useState<string>('');
  const [taskInstancesToDisplay, setTaskInstancesToDisplay] = useState<
    BasicTask[]
  >([]);
  const [showTaskDataLoading, setShowTaskDataLoading] =
    useState<boolean>(false);
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

  const {
    error: actionError,
    addError,
    removeError,
  }: {
    error: ErrorForDisplay | null;
    addError: Function;
    removeError: Function;
  } = useAPIError();

  const initializeTaskInstancesToDisplay = useCallback(
    (task: BasicTask | null) => {
      if (!task) {
        return;
      }
      HttpService.makeCallToBackend({
        path: `/tasks/${processInstanceId}/${task.guid}/task-instances`,
        httpMethod: 'GET',
        // reverse operates on self as well as return the new ordered array so reverse it right away
        successCallback: (results: BasicTask[]) =>
          setTaskInstancesToDisplay(results.reverse()),
        failureCallback: (err: any) => {
          setTaskDataToDisplay(`ERROR: ${err.message}`);
        },
      });
    },
    [processInstanceId],
  );

  const processTaskResult = (result: Task) => {
    if (result == null) {
      setTaskDataToDisplay('');
    } else {
      setTaskDataToDisplay(JSON.stringify(result.data, null, 2));
    }
    setShowTaskDataLoading(false);
  };

  const initializeTaskDataToDisplay = useCallback(
    (task: BasicTask | null) => {
      if (
        task &&
        ['COMPLETED', 'ERROR', 'READY'].includes(task.state) &&
        ability.can('GET', targetUris.processInstanceTaskDataPath)
      ) {
        setShowTaskDataLoading(true);
        HttpService.makeCallToBackend({
          path: `${targetUris.processInstanceTaskDataPath}/${task.guid}`,
          httpMethod: 'GET',
          successCallback: processTaskResult,
          failureCallback: (err: any) => {
            setTaskDataToDisplay(`ERROR: ${err.message}`);
            setShowTaskDataLoading(false);
          },
        });
      } else {
        setTaskDataToDisplay('');
      }
    },
    [ability, targetUris.processInstanceTaskDataPath],
  );

  const openTaskInspector = useCallback(
    (task: BasicTask) => {
      setTaskToDisplay(task);
      initializeTaskDataToDisplay(task);
      initializeTaskInstancesToDisplay(task);
    },
    [initializeTaskDataToDisplay, initializeTaskInstancesToDisplay],
  );

  const hideTaskInspector = useCallback(() => {
    setTaskToDisplay(null);
  }, []);

  const resetTaskActionDetails = () => {
    setEditingTaskData(false);
    setSelectingEvent(false);
    setAddingPotentialOwners(false);
    initializeTaskDataToDisplay(taskToDisplay);
    initializeTaskInstancesToDisplay(taskToDisplay);
    setEventPayload('{}');
    setAdditionalPotentialOwners(null);
    removeError();
  };

  const closeTaskInspector = () => {
    setTaskToDisplay(null);
    initializeTaskDataToDisplay(null);
    initializeTaskInstancesToDisplay(null);
    if (editingTaskData || selectingEvent || addingPotentialOwners) {
      resetTaskActionDetails();
    }
  };

  const getTaskById = (taskId: string) => {
    if (tasks !== null) {
      return tasks.find((task: BasicTask) => task.guid === taskId) || null;
    }
    return null;
  };

  const processScriptUnitTestCreateResult = (result: any) => {
    console.log('result', result);
  };

  const getParentTaskFromTask = (task: BasicTask) => {
    return task.properties_json.parent;
  };

  const createScriptUnitTest = () => {
    if (taskToDisplay) {
      const previousTask: BasicTask | null = getTaskById(
        getParentTaskFromTask(taskToDisplay),
      );
      const postBody = {
        bpmn_task_identifier: taskToDisplay.bpmn_identifier,
        previous_task_guid: previousTask?.guid,
        task_guid: taskToDisplay.guid,
      };
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}/script-unit-tests`,
        httpMethod: 'POST',
        successCallback: processScriptUnitTestCreateResult,
        postBody: postBody,
      });
    }
  };

  const isActiveTask = (task: BasicTask) => {
    const subprocessTypes = [
      'Subprocess',
      'CallActivity',
      'Transactional Subprocess',
    ];
    return (
      (task.state === 'WAITING' &&
        subprocessTypes.filter((type) => type === task.typename).length > 0) ||
      task.state === 'READY' ||
      (processInstance &&
        processInstance.status === 'suspended' &&
        task.state === 'ERROR')
    );
  };

  const canEditTaskData = (task: BasicTask) => {
    return (
      processInstance &&
      ability.can('PUT', targetUris.processInstanceTaskDataPath) &&
      isActiveTask(task) &&
      processInstance.status === 'suspended' &&
      showingActiveTask
    );
  };

  const canSendEvent = (task: BasicTask) => {
    // We actually could allow this for any waiting events
    const taskTypes = ['EventBasedGateway'];
    return (
      !selectingEvent &&
      processInstance &&
      processInstance.status === 'waiting' &&
      ability.can('POST', targetUris.processInstanceSendEventPath) &&
      taskTypes.filter((type) => type === task.typename).length > 0 &&
      task.state === 'WAITING' &&
      showingActiveTask
    );
  };

  const canCompleteTask = (task: BasicTask) => {
    return (
      processInstance &&
      processInstance.status === 'suspended' &&
      ability.can('POST', targetUris.processInstanceCompleteTaskPath) &&
      isActiveTask(task) &&
      showingActiveTask
    );
  };

  const canAddPotentialOwners = (task: BasicTask) => {
    return (
      HUMAN_TASK_TYPES.includes(task.typename) &&
      processInstance &&
      processInstance.status === 'suspended' &&
      ability.can('POST', targetUris.processInstanceTaskAssignPath) &&
      isActiveTask(task) &&
      showingActiveTask
    );
  };
  const canResetProcess = (task: BasicTask) => {
    return (
      ability.can('POST', targetUris.processInstanceResetPath) &&
      processInstance &&
      processInstance.status === 'suspended' &&
      ((task.state === 'READY' && !showingActiveTask) ||
        (task.state === 'ERROR' && showingActiveTask))
    );
  };

  const getEvents = (task: BasicTask) => {
    const handleMessage = (eventDefinition: EventDefinition) => {
      if (EVENTS_THAT_NEED_PAYLOAD.includes(eventDefinition.typename)) {
        const newEvent = eventDefinition;
        delete newEvent.message_var;
        newEvent.payload = {};
        return newEvent;
      }
      return eventDefinition;
    };
    const eventDefinition =
      task.task_definition_properties_json.event_definition;
    if (eventDefinition && eventDefinition.event_definitions) {
      return eventDefinition.event_definitions.map((e: EventDefinition) =>
        handleMessage(e),
      );
    }
    if (eventDefinition) {
      return [handleMessage(eventDefinition)];
    }
    return [];
  };

  const saveTaskDataResult = (_: any) => {
    setEditingTaskData(false);
  };

  const saveTaskData = () => {
    if (!taskToDisplay) {
      return;
    }
    removeError();

    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceTaskDataPath}/${taskToDisplay.guid}`,
      httpMethod: 'PUT',
      successCallback: saveTaskDataResult,
      failureCallback: addError,
      postBody: {
        new_task_data: taskDataToDisplay,
      },
    });
  };

  const addPotentialOwners = () => {
    if (!additionalPotentialOwners || additionalPotentialOwners.length === 0) {
      addError({
        message: 'Please select a user from the dropdown',
      });
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
    if ('payload' in eventToSend) {
      try {
        eventToSend.payload = JSON.parse(eventPayload);
      } catch (err) {
        addError({
          message: `Invalid JSON payload: ${(err as Error).message}`,
        });
        return;
      }
    }
    HttpService.makeCallToBackend({
      path: targetUris.processInstanceSendEventPath,
      httpMethod: 'POST',
      successCallback: onSendEventSuccess,
      failureCallback: addError,
      postBody: eventToSend,
    });
  };

  const completeTask = (execute: boolean) => {
    if (taskToDisplay) {
      HttpService.makeCallToBackend({
        path: `/task-complete/${modifiedProcessModelId}/${processInstanceId}/${taskToDisplay.guid}`,
        httpMethod: 'POST',
        successCallback: onCompleteTaskSuccess,
        postBody: { execute },
      });
    }
  };

  const switchToTask = (
    taskGuid: string,
    taskListToUse: BasicTask[] | null,
  ) => {
    if (taskListToUse && taskToDisplay) {
      const task = taskListToUse.find(
        (task_: BasicTask) => task_.guid === taskGuid,
      );
      if (task) {
        // set to null right away to hopefully avoid using the incorrect task later
        setTaskToDisplay(null);
        setTaskToDisplay(task);
        initializeTaskDataToDisplay(task);
      }
    }
  };

  const handleEventChange = (typename: string, candidateEvents: any[]) => {
    const selectedItem = candidateEvents.find(
      (item: any) => item.typename === typename,
    );
    setEventToSend(selectedItem);
    setEventTextEditorEnabled(
      EVENTS_THAT_NEED_PAYLOAD.includes(selectedItem.typename),
    );
  };

  const dialogProps: TaskInspectorDialogProps = {
    taskToDisplay,
    taskDataToDisplay,
    taskInstancesToDisplay,
    showTaskDataLoading,
    editingTaskData,
    selectingEvent,
    addingPotentialOwners,
    eventToSend,
    eventPayload,
    eventTextEditorEnabled,
    tasks,
    actionError,
    candidateEvents: taskToDisplay ? getEvents(taskToDisplay) : [],
    canCreateScriptUnitTest:
      !!taskToDisplay &&
      taskToDisplay.typename === 'ScriptTask' &&
      ability.can('PUT', targetUris.processModelShowPath),
    canEditTaskData: !!taskToDisplay && !!canEditTaskData(taskToDisplay),
    canAddPotentialOwners:
      !!taskToDisplay && !!canAddPotentialOwners(taskToDisplay),
    canCompleteTask: !!taskToDisplay && !!canCompleteTask(taskToDisplay),
    canSendEvent: !!taskToDisplay && !!canSendEvent(taskToDisplay),
    canResetProcess: !!taskToDisplay && !!canResetProcess(taskToDisplay),
    completionViewBaseUrl,
    completionQueryParams,
    onClose: closeTaskInspector,
    onHideTask: hideTaskInspector,
    onTaskDataChange: (value: string) => setTaskDataToDisplay(value || ''),
    onStartEditTaskData: () => setEditingTaskData(true),
    onStartAddingPotentialOwners: () => setAddingPotentialOwners(true),
    onStartSelectingEvent: () => setSelectingEvent(true),
    onCancelAction: resetTaskActionDetails,
    onSaveTaskData: saveTaskData,
    onAddPotentialOwners: addPotentialOwners,
    onSelectUser: (user: User) => {
      setAdditionalPotentialOwners([user]);
      removeError();
    },
    onSendEvent: sendEvent,
    onCompleteTask: completeTask,
    onResetProcess,
    onCreateScriptUnitTest: createScriptUnitTest,
    onNavigateCallActivity,
    onEventChange: handleEventChange,
    onEventPayloadChange: (value: any) => setEventPayload(value || '{}'),
    onSwitchTask: switchToTask,
  };

  return { openTaskInspector, dialogProps };
}

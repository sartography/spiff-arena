import { ReactElement, useCallback, useEffect, useState } from 'react';
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
  Reset,
  RuleDraft,
  SkipForward,
  StopOutline,
  Warning,
  View,
} from '@carbon/icons-react';
import {
  Grid,
  Box,
  Typography,
  IconButton,
  Button,
  Chip,
  CircularProgress,
  Tabs,
  Tab,
  MenuItem,
  Select,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import {
  DeleteOutlineOutlined,
  LinkOutlined,
  PauseOutlined,
  PlayArrow,
  SyncAltOutlined,
  StopCircleOutlined,
} from '@mui/icons-material';
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
  MULTI_INSTANCE_TASK_TYPES,
  LOOP_TASK_TYPES,
  titleizeString,
  isURL,
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
  ProcessModel,
  Task,
  User,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import ProcessInstanceClass from '../classes/ProcessInstanceClass';
import TaskListTable from '../components/TaskListTable';
import useAPIError from '../hooks/UseApiError';
import UserSearch from '../components/UserSearch';
import ProcessInstanceLogList from '../components/ProcessInstanceLogList';
import MessageInstanceList from '../components/messages/MessageInstanceList';
import {
  childrenForErrorObject,
  errorForDisplayFromString,
} from '../components/ErrorDisplay';
import { Notification } from '../components/Notification';
import DateAndTimeService from '../services/DateAndTimeService';
import ProcessInstanceCurrentTaskInfo from '../components/ProcessInstanceCurrentTaskInfo';
import useKeyboardShortcut from '../hooks/useKeyboardShortcut';
import useProcessInstanceNavigate from '../hooks/useProcessInstanceNavigate';
import SpiffTooltip from '../components/SpiffTooltip';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceShow({ variant }: OwnProps) {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { navigateToInstance } = useProcessInstanceNavigate();

  const eventsThatNeedPayload = ['MessageEventDefinition'];

  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);
  const [tasks, setTasks] = useState<Task[] | null>(null);
  const [tasksCallHadError, setTasksCallHadError] = useState<boolean>(false);
  const [taskToDisplay, setTaskToDisplay] = useState<Task | null>(null);
  const [taskToTimeTravelTo, setTaskToTimeTravelTo] = useState<Task | null>(
    null,
  );
  const [taskDataToDisplay, setTaskDataToDisplay] = useState<string>('');
  const [taskInstancesToDisplay, setTaskInstancesToDisplay] = useState<Task[]>(
    [],
  );
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
    `${params.process_model_id}`,
  );

  const modifiedProcessModelId = params.process_model_id;
  const processModelId = unModifyProcessIdentifierForPathParam(
    params.process_model_id ? params.process_model_id : '',
  );

  const { targetUris } = useUriListForPermissions();
  const taskListPath =
    variant === 'all'
      ? targetUris.processInstanceTaskListPath
      : targetUris.processInstanceTaskListForMePath;

  const permissionRequestData: PermissionsToCheck = {
    [`${targetUris.processInstanceMigratePath}`]: ['POST'],
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
    [targetUris.processModelFileCreatePath]: ['GET'],
    [taskListPath]: ['GET'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  const navigateToProcessInstances = (_result: any) => {
    navigate(
      `/process-instances?process_model_identifier=${unModifiedProcessModelId}`,
    );
  };

  const onProcessInstanceForceRun = (
    processInstanceResult: ProcessInstance,
  ) => {
    if (processInstanceResult.process_model_uses_queued_execution) {
      navigateToInstance({
        processInstanceId: processInstanceResult.id,
        suffix: '/progress',
      });
    } else {
      navigateToInstance({
        processInstanceId: processInstanceResult.id,
        suffix: '/interstitial',
      });
    }
  };

  const forceRunProcessInstance = () => {
    if (ability.can('POST', targetUris.processInstanceActionPath)) {
      HttpService.makeCallToBackend({
        path: `${targetUris.processInstanceActionPath}/run?force_run=true`,
        successCallback: onProcessInstanceForceRun,
        httpMethod: 'POST',
      });
    }
  };

  const shortcutLoadPrimaryFile = () => {
    if (ability.can('GET', targetUris.processInstanceActionPath)) {
      const processResult = (result: ProcessModel) => {
        const primaryFileName = result.primary_file_name;
        if (!primaryFileName) {
          // this should be very unlikely, since we are in the context of an instance,
          // but it's techically possible for the file to have been subsequently deleted or something.
          console.error('Primary file name not found for the process model.');
          return;
        }
        navigate(
          `/process-models/${modifiedProcessModelId}/files/${primaryFileName}`,
        );
      };
      HttpService.makeCallToBackend({
        path: `/process-models/${modifiedProcessModelId}`,
        successCallback: processResult,
      });
    }
  };

  const keyboardShortcuts: KeyboardShortcuts = {
    'f,r,enter': {
      function: forceRunProcessInstance,
      label: '[F]orce [r]un process instance',
    },
    'd,enter': {
      function: shortcutLoadPrimaryFile,
      label: 'View process model [d]iagram',
    },
  };
  const keyboardShortcutArea = useKeyboardShortcut(keyboardShortcuts);

  let processInstanceShowPageBaseUrl = `/process-instances/for-me/${params.process_model_id}/${params.process_instance_id}`;
  const processInstanceShowPageBaseUrlAllVariant = `/process-instances/${params.process_model_id}/${params.process_instance_id}`;
  if (variant === 'all') {
    processInstanceShowPageBaseUrl = processInstanceShowPageBaseUrlAllVariant;
  }

  const bpmnProcessGuid = searchParams.get('bpmn_process_guid');
  const tab = searchParams.get('tab');
  const taskSubTab = searchParams.get('taskSubTab');
  const processIdentifier = searchParams.get('process_identifier');

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
          (task: Task) => task.guid === params.to_task_guid,
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
    taskListPath,
    bpmnProcessGuid,
  ]);

  const getProcessInstance = useCallback(() => {
    let queryParams = '';
    if (processIdentifier) {
      queryParams = `?process_identifier=${processIdentifier}`;
    }
    let apiPath = '/process-instances/for-me';
    if (variant === 'all') {
      apiPath = '/process-instances';
    }
    HttpService.makeCallToBackend({
      path: `${apiPath}/${modifiedProcessModelId}/${params.process_instance_id}${queryParams}`,
      successCallback: (p: ProcessInstance) => {
        setProcessInstance(p);
      },
    });
  }, [
    params.process_instance_id,
    modifiedProcessModelId,
    variant,
    processIdentifier,
  ]);

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

    if (tab) {
      setSelectedTabIndex(parseInt(tab || '0', 10));
    }
    if (taskSubTab) {
      setSelectedTaskTabSubTab(parseInt(taskSubTab || '0', 10));
    }
    return undefined;
  }, [
    permissionsLoaded,
    getActionableTaskList,
    getProcessInstance,
    tab,
    taskSubTab,
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
    const queryParamArray = [];
    if (processIdentifier) {
      queryParamArray.push(`process_identifier=${processIdentifier}`);
    }
    if (bpmnProcessGuid) {
      queryParamArray.push(`bpmn_process_guid=${bpmnProcessGuid}`);
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

  const formatMetadataValue = (key: string, value: string) => {
    if (isURL(value)) {
      return (
        <a href={value} target="_blank" rel="noopener noreferrer">
          {key} link
        </a>
      );
    }
    return value;
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
        <Typography component="dt" variant="subtitle2">
          {lastUpdatedTimeLabel}:
        </Typography>
        <Typography component="dd" variant="body2">
          {DateAndTimeService.convertSecondsToFormattedDateTime(
            lastUpdatedTime || 0,
          ) || 'N/A'}
        </Typography>
      </dl>
    );

    let statusIcon = <InProgress />;
    // let statusColor = 'default';
    if (processInstance.status === 'suspended') {
      statusIcon = <PauseOutline />;
    } else if (processInstance.status === 'complete') {
      statusIcon = <Checkmark />;
      // statusColor = 'success';
    } else if (processInstance.status === 'terminated') {
      statusIcon = <StopOutline />;
    } else if (processInstance.status === 'error') {
      statusIcon = <Warning />;
      // statusColor = 'error';
    }

    const [lastMilestoneFullValue, lastMilestoneTruncatedValue] =
      getLastMilestoneFromProcessInstance(
        processInstance,
        processInstance.last_milestone_bpmn_name,
      );

    return (
      <Grid container spacing={2}>
        <Grid item xs={12} sm={6}>
          <dl>
            <Typography component="dt" variant="subtitle2">
              Status:
            </Typography>
            <Typography component="dd" variant="body2">
              <Chip
                label={`${processInstance.status}`}
                icon={statusIcon}
                // color={statusColor}
                size="small"
              />
            </Typography>
          </dl>
          <dl>
            <Typography component="dt" variant="subtitle2">
              Started by:
            </Typography>
            <Typography component="dd" variant="body2">
              {' '}
              {processInstance.process_initiator_username}
            </Typography>
          </dl>
          {processInstance.process_model_with_diagram_identifier ? (
            <dl>
              <Typography component="dt" variant="subtitle2">
                Current diagram:{' '}
              </Typography>
              <Typography component="dd" variant="body2">
                <Link
                  data-qa="go-to-current-diagram-process-model"
                  to={`/process-models/${modifyProcessIdentifierForPathParam(
                    processInstance.process_model_with_diagram_identifier || '',
                  )}`}
                >
                  {processInstance.process_model_with_diagram_identifier}
                </Link>
              </Typography>
            </dl>
          ) : null}
          <dl>
            <Typography component="dt" variant="subtitle2">
              Started:
            </Typography>
            <Typography component="dd" variant="body2">
              {DateAndTimeService.convertSecondsToFormattedDateTime(
                processInstance.start_in_seconds || 0,
              )}
            </Typography>
          </dl>
          {lastUpdatedTimeTag}
          <dl>
            <Typography component="dt" variant="subtitle2">
              Last milestone:
            </Typography>
            <Typography
              component="dd"
              variant="body2"
              title={lastMilestoneFullValue}
            >
              {lastMilestoneTruncatedValue}
            </Typography>
          </dl>
          <dl>
            <Typography component="dt" variant="subtitle2">
              Revision:
            </Typography>
            <Typography component="dd" variant="body2">
              {processInstance.bpmn_version_control_identifier} (
              {processInstance.bpmn_version_control_type})
            </Typography>
          </dl>
        </Grid>
        <Grid item xs={12} sm={6}>
          {(processInstance.process_metadata || []).map(
            (processInstanceMetadata) => (
              <dl className="metadata-display">
                <Typography
                  component="dt"
                  variant="subtitle2"
                  title={processInstanceMetadata.key}
                >
                  {truncateString(processInstanceMetadata.key, 50)}:
                </Typography>
                <Typography
                  component="dd"
                  variant="body2"
                  data-qa={`metadata-value-${processInstanceMetadata.key}`}
                >
                  {formatMetadataValue(
                    processInstanceMetadata.key,
                    processInstanceMetadata.value,
                  )}
                </Typography>
              </dl>
            ),
          )}
        </Grid>
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

  const navigateToProcessInstanceMigratePage = () => {
    navigate(
      `/process-instances/${params.process_model_id}/${params.process_instance_id}/migrate`,
    );
  };

  const terminateButton = () => {
    if (
      processInstance &&
      !ProcessInstanceClass.terminalStatuses().includes(processInstance.status)
    ) {
      return (
        <ButtonWithConfirmation
          renderIcon={<StopCircleOutlined />}
          iconDescription="Terminate"
          hasIconOnly
          description={`Terminate Process Instance: ${processInstance.id}`}
          onConfirmation={terminateProcessInstance}
          confirmButtonLabel="Terminate"
        />
      );
    }
    return null;
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
        <SpiffTooltip title="Suspend" placement="top">
          <IconButton onClick={suspendProcessInstance} aria-label="Suspend">
            <PauseOutlined />
          </IconButton>
        </SpiffTooltip>
      );
    }
    return null;
  };
  const migrateButton = () => {
    if (processInstance && processInstance.status === 'suspended') {
      return (
        <SpiffTooltip title="Migrate" placement="top">
          <IconButton
            onClick={navigateToProcessInstanceMigratePage}
            aria-label="Migrate"
          >
            <SyncAltOutlined />
          </IconButton>
        </SpiffTooltip>
      );
    }
    return null;
  };

  const copyProcessInstanceShortLinkButton = () => {
    return (
      <SpiffTooltip title="Copy shareable short link" placement="top">
        <IconButton
          onClick={copyProcessInstanceShortLink}
          aria-label="Copy shareable short link"
        >
          <LinkOutlined />
        </IconButton>
      </SpiffTooltip>
    );
  };

  const resumeButton = () => {
    if (processInstance && processInstance.status === 'suspended') {
      return (
        <SpiffTooltip title="Resume" placement="top">
          <IconButton onClick={resumeProcessInstance} aria-label="Resume">
            <PlayArrow />
          </IconButton>
        </SpiffTooltip>
      );
    }
    return null;
  };

  const deleteButton = () => {
    if (
      processInstance &&
      ProcessInstanceClass.terminalStatuses().includes(processInstance.status)
    ) {
      return (
        <ButtonWithConfirmation
          data-qa="process-instance-delete"
          renderIcon={<DeleteOutlineOutlined />}
          iconDescription="Delete"
          hasIconOnly
          description={`Delete Process Instance: ${processInstance.id}`}
          onConfirmation={deleteProcessInstance}
          confirmButtonLabel="Delete"
        />
      );
    }
    return null;
  };

  const initializeTaskInstancesToDisplay = useCallback(
    (task: Task | null) => {
      if (!task) {
        return;
      }
      HttpService.makeCallToBackend({
        path: `/tasks/${params.process_instance_id}/${task.guid}/task-instances`,
        httpMethod: 'GET',
        // reverse operates on self as well as return the new ordered array so reverse it right away
        successCallback: (results: Task[]) =>
          setTaskInstancesToDisplay(results.reverse()),
        failureCallback: (error: any) => {
          setTaskDataToDisplay(`ERROR: ${error.message}`);
        },
      });
    },
    [params.process_instance_id],
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
    (task: Task | null) => {
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
          failureCallback: (error: any) => {
            setTaskDataToDisplay(`ERROR: ${error.message}`);
            setShowTaskDataLoading(false);
          },
        });
      } else {
        setTaskDataToDisplay('');
      }
    },
    [ability, targetUris.processInstanceTaskDataPath],
  );

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
              errorForDisplayFromString(
                processDataToDisplay.process_data_value,
              ),
            )}
          </>
        );
      }
      return (
        <Dialog
          className="wide-dialog"
          open={!!processDataToDisplay}
          onClose={handleProcessDataDisplayClose}
        >
          <DialogTitle>
            Data Object: {processDataToDisplay.process_data_identifier}
          </DialogTitle>
          <DialogContent>{bodyComponent}</DialogContent>
        </Dialog>
      );
    }
    return null;
  };

  const handleProcessDataShowResponse = (processData: ProcessData) => {
    setProcessDataToDisplay(processData);
  };

  const handleProcessDataShowReponseUnauthorized = (
    dataObjectIdentifer: string,
    result: any,
  ) => {
    const processData: ProcessData = {
      process_data_identifier: dataObjectIdentifer,
      process_data_value: result.message,
      authorized: false,
    };
    setProcessDataToDisplay(processData);
  };

  const makeProcessDataCallFromShapeElement = useCallback(
    (shapeElement: any) => {
      const { dataObjectRef } = shapeElement.businessObject;
      let category = 'default';
      if ('extensionElements' in dataObjectRef) {
        const categoryExtension = dataObjectRef.extensionElements.values.find(
          (extension: any) => {
            return extension.$type === 'spiffworkflow:category';
          },
        );
        if (categoryExtension) {
          category = categoryExtension.$body;
        }
      }
      const dataObjectIdentifer = dataObjectRef.id;
      const parentProcess = shapeElement.businessObject.$parent;
      const parentProcessIdentifier = parentProcess.id;

      let additionalParams = '';
      if (tasks) {
        const matchingTask: Task | undefined = tasks.find((task: Task) => {
          return task.bpmn_identifier === parentProcessIdentifier;
        });
        if (matchingTask) {
          additionalParams = `?process_identifier=${parentProcessIdentifier}&bpmn_process_guid=${matchingTask.guid}`;
        } else if (processIdentifier && bpmnProcessGuid) {
          additionalParams = `?process_identifier=${processIdentifier}&bpmn_process_guid=${bpmnProcessGuid}`;
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
    },
    [
      addError,
      params.process_instance_id,
      params.process_model_id,
      tasks,
      bpmnProcessGuid,
      processIdentifier,
    ],
  );

  const findMatchingTaskFromShapeElement = useCallback(
    (shapeElement: any, bpmnProcessIdentifiers: any) => {
      if (tasks) {
        const matchingTask: Task | undefined = tasks.find((task: Task) => {
          return (
            task.bpmn_identifier === shapeElement.id &&
            bpmnProcessIdentifiers.includes(
              task.bpmn_process_definition_identifier,
            )
          );
        });
        return matchingTask;
      }
      return undefined;
    },
    [tasks],
  );

  const handleCallActivityNavigate = useCallback(
    (task: Task, event: any) => {
      if (
        task &&
        task.typename === 'CallActivity' &&
        !['FUTURE', 'LIKELY', 'MAYBE'].includes(task.state)
      ) {
        const processIdentifierToUse =
          task.task_definition_properties_json.spec;
        const url = `${window.location.pathname}?process_identifier=${processIdentifierToUse}&bpmn_process_guid=${task.guid}`;
        if (event.type === 'auxclick') {
          window.open(url);
        } else {
          setTasks(null);
          setProcessInstance(null);
          navigate(url);
        }
      }
    },
    [navigate],
  );

  const handleClickedDiagramTask = useCallback(
    (shapeElement: any, bpmnProcessIdentifiers: any) => {
      if (shapeElement.type === 'bpmn:DataObjectReference') {
        makeProcessDataCallFromShapeElement(shapeElement);
      } else if (tasks) {
        const matchingTask = findMatchingTaskFromShapeElement(
          shapeElement,
          bpmnProcessIdentifiers,
        );
        if (matchingTask) {
          setTaskToDisplay(matchingTask);
          initializeTaskDataToDisplay(matchingTask);
          initializeTaskInstancesToDisplay(matchingTask);
        }
      }
    },
    [
      findMatchingTaskFromShapeElement,
      initializeTaskDataToDisplay,
      initializeTaskInstancesToDisplay,
      makeProcessDataCallFromShapeElement,
      tasks,
    ],
  );

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

  const handleTaskDataDisplayClose = () => {
    setTaskToDisplay(null);
    initializeTaskDataToDisplay(null);
    initializeTaskInstancesToDisplay(null);
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
        getParentTaskFromTask(taskToDisplay),
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
    if ('payload' in eventToSend) {
      eventToSend.payload = JSON.parse(eventPayload);
    }
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
          variant="outlined"
          startIcon={<RuleDraft />}
          data-qa="create-script-unit-test-button"
          onClick={createScriptUnitTest}
        >
          Create Script Unit Test
        </Button>,
      );
    }

    if (
      task.typename === 'CallActivity' &&
      !['FUTURE', 'LIKELY', 'MAYBE'].includes(task.state)
    ) {
      buttons.push(
        <Button
          variant="outlined"
          className="button-link indented-content"
          onAuxClick={(event: any) => {
            handleCallActivityNavigate(task, event);
          }}
          onClick={(event: any) => {
            setTaskToDisplay(null);
            handleCallActivityNavigate(task, event);
          }}
        >
          View Call Activity Diagram
        </Button>,
      );
    }

    if (canEditTaskData(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Edit />}
          data-qa="edit-task-data-button"
          onClick={() => setEditingTaskData(true)}
        >
          Edit Task Data
        </Button>,
      );
    }
    if (canAddPotentialOwners(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<UserFollow />}
          title="Allow an additional user to complete this task"
          data-qa="add-potential-owners-button"
          onClick={() => setAddingPotentialOwners(true)}
        >
          Assign user
        </Button>,
      );
    }
    if (canCompleteTask(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Play />}
          data-qa="execute-task-complete-button"
          onClick={() => completeTask(true)}
        >
          Execute Task
        </Button>,
      );
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<SkipForward />}
          data-qa="mark-task-complete-button"
          onClick={() => completeTask(false)}
        >
          Skip Task
        </Button>,
      );
    }
    if (canSendEvent(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Send />}
          data-qa="select-event-button"
          onClick={() => setSelectingEvent(true)}
        >
          Send Event
        </Button>,
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
          variant="outlined"
          startIcon={<Reset />}
          title={titleText}
          data-qa="reset-process-button"
          onClick={() => resetProcessInstance()}
        >
          Reset Process Here
        </Button>,
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
        {showTaskDataLoading ? <CircularProgress size={24} /> : null}
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
      <Box>
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
      </Box>
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
      <Box>
        <h3 className="task-data-details-header">Choose event to send</h3>
        <div className="indented-content">
          <p className="explanatory-message with-tiny-bottom-margin">
            Select an event to send. A message event will require a body as
            well.
          </p>
          <Select
            id="process-instance-select-event"
            className={className}
            value={eventToSend}
            onChange={(event) => {
              const selectedItem = candidateEvents.find(
                (item: any) => item.typename === event.target.value,
              );
              setEventToSend(selectedItem);
              setEventTextEditorEnabled(
                eventsThatNeedPayload.includes(selectedItem.typename),
              );
            }}
          >
            {candidateEvents.map((item: any) => (
              <MenuItem key={item.typename} value={item.typename}>
                {item.name || item.label || item.typename}
              </MenuItem>
            ))}
          </Select>
          {editor}
        </div>
      </Box>
    );
  };

  const taskIsInstanceOfMultiInstanceTask = (task: Task) => {
    // this is the same check made in the backend in the _process_instance_task_list method to determine
    // if the given task is an instance of a multi-instance or loop task.
    // we need to avoid resetting the task instance list since the list may not be the same as we need
    return 'instance' in task.runtime_info || 'iteration' in task.runtime_info;
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

  const switchToTask = (taskGuid: string, taskListToUse: Task[] | null) => {
    if (taskListToUse && taskToDisplay) {
      const task = taskListToUse.find((t: Task) => t.guid === taskGuid);
      if (task) {
        // set to null right away to hopefully avoid using the incorrect task later
        setTaskToDisplay(null);
        setTaskToDisplay(task);
        initializeTaskDataToDisplay(task);
      }
    }
  };
  const createButtonSetForTaskInstances = () => {
    if (taskInstancesToDisplay.length === 0 || !taskToDisplay) {
      return null;
    }
    return (
      <>
        {taskInstancesToDisplay.map((task: Task, index: number) => {
          const buttonClass =
            task.guid === taskToDisplay.guid ? 'selected-task-instance' : null;
          return (
            <Grid container spacing={2}>
              <Grid item xs={1}>
                <SpiffTooltip title="View">
                  <IconButton
                    onClick={() =>
                      switchToTask(task.guid, taskInstancesToDisplay)
                    }
                  >
                    <View />
                  </IconButton>
                </SpiffTooltip>
              </Grid>
              <Grid item xs={11}>
                <div className={`task-instance-modal-row-item ${buttonClass}`}>
                  {index + 1} {': '}
                  {DateAndTimeService.convertSecondsToFormattedDateTime(
                    task.properties_json.last_state_change,
                  )}{' '}
                  {' - '} {task.state}
                </div>
              </Grid>
            </Grid>
          );
        })}
      </>
    );
  };

  const createButtonsForMultiTasks = (
    instances: number[],
    infoType: string,
  ) => {
    if (!tasks || !taskToDisplay) {
      return [];
    }
    return instances.map((v: any) => {
      return (
        <Button
          variant="outlined"
          key={`btn-switch-instance-${infoType}-${v}`}
          onClick={() =>
            switchToTask(taskToDisplay.runtime_info.instance_map[v], tasks)
          }
        >
          {v + 1}
        </Button>
      );
    });
  };

  const taskInstanceSelector = () => {
    if (!taskToDisplay) {
      return null;
    }

    const accordionItems = [];

    if (
      !taskIsInstanceOfMultiInstanceTask(taskToDisplay) &&
      taskInstancesToDisplay.length > 0
    ) {
      accordionItems.push(
        <Accordion key="mi-task-instances">
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            Task instances ({taskInstancesToDisplay.length})
          </AccordionSummary>
          <AccordionDetails>
            {createButtonSetForTaskInstances()}
          </AccordionDetails>
        </Accordion>,
      );
    }

    if (MULTI_INSTANCE_TASK_TYPES.includes(taskToDisplay.typename)) {
      ['completed', 'running', 'future'].forEach((infoType: string) => {
        let taskInstances: ReactElement[] = [];
        const infoArray = taskToDisplay.runtime_info[infoType];
        taskInstances = createButtonsForMultiTasks(infoArray, infoType);
        accordionItems.push(
          <Accordion key={`mi-instance-${titleizeString(infoType)}`}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              {`${titleizeString(infoType)} instances for MI task (${
                taskInstances.length
              })`}
            </AccordionSummary>
            <AccordionDetails>{taskInstances}</AccordionDetails>
          </Accordion>,
        );
      });
    }
    if (LOOP_TASK_TYPES.includes(taskToDisplay.typename)) {
      const loopTaskInstanceIndexes = [
        ...Array(taskToDisplay.runtime_info.iterations_completed).keys(),
      ];
      const buttons = createButtonsForMultiTasks(
        loopTaskInstanceIndexes,
        'mi-loop-iterations',
      );
      let text = '';
      if (
        typeof taskToDisplay.runtime_info.iterations_remaining !==
          'undefined' &&
        taskToDisplay.state !== 'COMPLETED'
      ) {
        text += `${taskToDisplay.runtime_info.iterations_remaining} remaining`;
      }
      accordionItems.push(
        <Accordion key="mi-loop-iterations">
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            Loop iterations ({buttons.length})
          </AccordionSummary>
          <AccordionDetails>
            <div>{text}</div>
            <div>{buttons}</div>
          </AccordionDetails>
        </Accordion>,
      );
    }
    if (accordionItems.length > 0) {
      return <Box>{accordionItems}</Box>;
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
    if (editingTaskData) {
      primaryButtonText = 'Save';
      secondaryButtonText = 'Cancel';
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = saveTaskData;
    } else if (selectingEvent) {
      primaryButtonText = 'Send';
      secondaryButtonText = 'Cancel';
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = sendEvent;
    } else if (addingPotentialOwners) {
      primaryButtonText = 'Add';
      secondaryButtonText = 'Cancel';
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = addPotentialOwners;
    }
    if (taskToUse.runtime_info) {
      if (typeof taskToUse.runtime_info.instance !== 'undefined') {
        secondaryButtonText = 'Return to MultiInstance Task';
        onSecondarySubmit = () => {
          switchToTask(taskToUse.properties_json.parent, [
            ...(tasks || []),
            ...taskInstancesToDisplay,
          ]);
        };
      } else if (typeof taskToUse.runtime_info.iteration !== 'undefined') {
        secondaryButtonText = 'Return to Loop Task';
        onSecondarySubmit = () => {
          switchToTask(taskToUse.properties_json.parent, [
            ...(tasks || []),
            ...taskInstancesToDisplay,
          ]);
        };
      }
    }

    return (
      <Dialog
        open={!!taskToUse}
        onClose={handleTaskDataDisplayClose}
        className="wide-dialog"
      >
        <DialogTitle>{`${taskToUse.bpmn_identifier} (${taskToUse.typename}): ${taskToUse.state}`}</DialogTitle>
        <DialogContent>
          <div className="indented-content explanatory-message">
            {taskToUse.bpmn_name ? (
              <div>
                <Box display="flex" gap={2}>
                  Name: {taskToUse.bpmn_name}
                </Box>
              </div>
            ) : null}

            <div>
              <Box display="flex" gap={2}>
                Guid: {taskToUse.guid}
              </Box>
            </div>
          </div>
          {taskDisplayButtons(taskToUse)}
          {taskToUse.state === 'COMPLETED' ? (
            <div className="indented-content">
              <Box display="flex" gap={2}>
                {completionViewLink(
                  'View process instance at the time when this task was active.',
                  taskToUse.guid,
                )}
              </Box>
              <br />
            </div>
          ) : null}
          <br />
          {taskActionDetails()}
          {taskInstanceSelector()}
        </DialogContent>
        <DialogActions>
          {secondaryButtonText && (
            <Button onClick={onSecondarySubmit} color="primary">
              {secondaryButtonText}
            </Button>
          )}
          <Button onClick={onRequestSubmit} color="primary" autoFocus>
            {primaryButtonText}
          </Button>
        </DialogActions>
      </Dialog>
    );
  };

  const buttonIcons = () => {
    if (!processInstance) {
      return null;
    }
    const elements = [];
    elements.push(copyProcessInstanceShortLinkButton());
    if (ability.can('POST', targetUris.processInstanceTerminatePath)) {
      elements.push(terminateButton());
    }
    if (ability.can('POST', targetUris.processInstanceSuspendPath)) {
      elements.push(suspendButton());
    }
    if (ability.can('POST', targetUris.processInstanceMigratePath)) {
      elements.push(migrateButton());
    }
    if (ability.can('POST', targetUris.processInstanceResumePath)) {
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
        <Grid container spacing={2}>
          <Grid item xs={12}>
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
          </Grid>
        </Grid>
        <br />
      </>
    );
  };

  const diagramArea = () => {
    if (!processInstance) {
      return null;
    }
    if (!tasks && !tasksCallHadError) {
      return <CircularProgress size={24} />;
    }

    const detailsComponent = (
      <>
        {childrenForErrorObject(
          errorForDisplayFromString(
            processInstance.bpmn_xml_file_contents_retrieval_error || '',
          ),
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
          diagramType="readonly"
          diagramXML={processInstance.bpmn_xml_file_contents || ''}
          onCallActivityOverlayClick={handleCallActivityNavigate}
          onElementClick={handleClickedDiagramTask}
          processModelId={processModelId || ''}
          tasks={tasks}
        />
        <div id="diagram-container" />
      </>
    );
  };

  const updateSelectedTab = (newTabIndex: any) => {
    // this causes the process instance and task list to render again as well
    // it'd be nice if we could find a way to avoid that
    updateSearchParams(newTabIndex, 'tab');
  };

  const updateSelectedTaskTabSubTab = (newTabIndex: any) => {
    updateSearchParams(newTabIndex, 'taskSubTab');
  };

  const taskTabSubTabs = () => {
    if (!processInstance) {
      return null;
    }

    return (
      <>
        <Tabs
          value={selectedTaskTabSubTab}
          onChange={(_, newValue) => updateSelectedTaskTabSubTab(newValue)}
        >
          <Tab label="Completed by me" />
          <Tab label="All completed" />
        </Tabs>
        <Box>
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
        </Box>
      </>
    );
  };

  // eslint-disable-next-line sonarjs/cognitive-complexity
  const getTabs = () => {
    if (!processInstance) {
      return null;
    }

    const canViewLogs = ability.can(
      'GET',
      targetUris.processInstanceLogListPath,
    );
    const canViewMsgs = ability.can('GET', targetUris.messageInstanceListPath);

    const getMessageDisplay = () => {
      if (canViewMsgs) {
        return <MessageInstanceList processInstanceId={processInstance.id} />;
      }
      return null;
    };

    return (
      <>
        <Tabs
          value={selectedTabIndex}
          onChange={(_, newValue) => updateSelectedTab(newValue)}
        >
          <Tab label="Diagram" />
          <Tab label="Milestones" disabled={!canViewLogs} />
          <Tab label="Events" disabled={!canViewLogs} />
          <Tab label="Messages" disabled={!canViewMsgs} />
          <Tab label="Tasks" />
        </Tabs>
        <Box>
          {selectedTabIndex === 0 ? diagramArea() : null}
          {selectedTabIndex === 1 ? (
            <ProcessInstanceLogList
              variant={variant}
              isEventsView={false}
              processModelId={modifiedProcessModelId || ''}
              processInstanceId={processInstance.id}
            />
          ) : null}
          {selectedTabIndex === 2 ? (
            <ProcessInstanceLogList
              variant={variant}
              isEventsView
              processModelId={modifiedProcessModelId || ''}
              processInstanceId={processInstance.id}
            />
          ) : null}
          {selectedTabIndex === 3 ? getMessageDisplay() : null}
          {selectedTabIndex === 4 ? taskTabSubTabs() : null}
        </Box>
      </>
    );
  };

  if (processInstance && permissionsLoaded) {
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
        <Box display="flex" alignItems="center" gap={1}>
          <Typography
            variant="h1"
            sx={{
              mr: '1rem',
            }}
          >
            Process Instance Id: {processInstance.id}
          </Typography>
          {buttonIcons()}
        </Box>
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

  return (
    // description="Active loading indicator"
    <CircularProgress style={{ margin: '50px 0 50px 50px' }} />
  );
}

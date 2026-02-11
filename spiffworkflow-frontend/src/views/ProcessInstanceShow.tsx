import { ReactElement, useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Editor } from '@monaco-editor/react';
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
import Grid from '@mui/material/Grid';
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
  getProcessStatus,
} from '../helpers';
import ConfirmIconButton from '../components/ConfirmIconButton';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  BasicTask,
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
  const [tasks, setTasks] = useState<BasicTask[] | null>(null);
  const [tasksCallHadError, setTasksCallHadError] = useState<boolean>(false);
  const [taskToDisplay, setTaskToDisplay] = useState<BasicTask | null>(null);
  const [taskToTimeTravelTo, setTaskToTimeTravelTo] =
    useState<BasicTask | null>(null);
  const [taskDataToDisplay, setTaskDataToDisplay] = useState<string>('');
  const [taskInstancesToDisplay, setTaskInstancesToDisplay] = useState<
    BasicTask[]
  >([]);
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
  const [diagramFileName, setDiagramFileName] = useState<string | null>(null);
  const [diagramProcessModelId, setDiagramProcessModelId] = useState<
    string | null
  >(null);
  const [diagramLoadError, setDiagramLoadError] = useState<string | null>(null);

  const [addingPotentialOwners, setAddingPotentialOwners] =
    useState<boolean>(false);
  const [additionalPotentialOwners, setAdditionalPotentialOwners] = useState<
    User[] | null
  >(null);

  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const [selectedTaskTabSubTab, setSelectedTaskTabSubTab] = useState<number>(0);
  const [copiedShortLinkToClipboard, setCopiedShortLinkToClipboard] =
    useState<boolean>(false);

  const { error, addError, removeError } = useAPIError();
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
  const { t } = useTranslation();

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
      label: t('force_run_process_instance'),
    },
    'd,enter': {
      function: shortcutLoadPrimaryFile,
      label: t('view_process_model_diagram'),
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
    const processTasksSuccess = (results: BasicTask[]) => {
      if (params.to_task_guid) {
        const matchingTask = results.find(
          (task: BasicTask) => task.guid === params.to_task_guid,
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

  useEffect(() => {
    if (!processInstance) {
      return;
    }

    if (processInstance.bpmn_xml_file_contents) {
      setDiagramFileName(null);
      setDiagramProcessModelId(null);
      setDiagramLoadError(null);
      return;
    }

    const diagramIdentifier =
      processInstance.process_model_with_diagram_identifier ||
      processInstance.process_model_identifier;
    if (!diagramIdentifier) {
      return;
    }

    const modifiedDiagramId =
      modifyProcessIdentifierForPathParam(diagramIdentifier);
    setDiagramProcessModelId(modifiedDiagramId);

    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedDiagramId}`,
      successCallback: (result: ProcessModel) => {
        if (result.primary_file_name) {
          setDiagramFileName(result.primary_file_name);
          setDiagramLoadError(null);
        } else {
          setDiagramLoadError(t('diagram_file_name_editor_error_required'));
        }
      },
      failureCallback: (err: { message?: string } | string) => {
        if (typeof err === 'string') {
          setDiagramLoadError(err);
        } else if (err?.message) {
          setDiagramLoadError(err.message);
        } else {
          setDiagramLoadError(t('failed_to_load_diagram'));
        }
      },
    });
  }, [processInstance, t]);

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
        data-testid="process-instance-step-link"
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
    let lastUpdatedTimeLabel = t('process_updated');
    let lastUpdatedTime = processInstance.task_updated_at_in_seconds;
    if (processInstance.end_in_seconds) {
      lastUpdatedTimeLabel = t('process_completed');
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
      getLastMilestoneFromProcessInstance(processInstance);

    return (
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <dl>
            <Typography component="dt" variant="subtitle2">
              {t('status')}:
            </Typography>
            <Typography component="dd" variant="body2">
              <Chip
                label={getProcessStatus(processInstance)}
                icon={statusIcon}
                data-testid="process-instance-status-chip"
                // color={statusColor}
                size="small"
              />
            </Typography>
          </dl>
          <dl>
            <Typography component="dt" variant="subtitle2">
              {t('started_by')}:
            </Typography>
            <Typography component="dd" variant="body2">
              {' '}
              {processInstance.process_initiator_username}
            </Typography>
          </dl>
          {processInstance.process_model_with_diagram_identifier ? (
            <dl>
              <Typography component="dt" variant="subtitle2">
                {t('current_diagram')}:{' '}
              </Typography>
              <Typography component="dd" variant="body2">
                <Link
                  data-testid="go-to-current-diagram-process-model"
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
              {t('started')}:
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
              {t('last_milestone')}:
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
              {t('revision')}:
            </Typography>
            <Typography component="dd" variant="body2">
              {processInstance.bpmn_version_control_identifier} (
              {processInstance.bpmn_version_control_type})
            </Typography>
          </dl>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
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
                  data-testid={`metadata-value-${processInstanceMetadata.key}`}
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
        <ConfirmIconButton
          renderIcon={<StopCircleOutlined />}
          iconDescription={t('terminate_button')}
          description={t('terminate_process_instance', {
            id: processInstance.id,
          })}
          onConfirmation={terminateProcessInstance}
          confirmButtonLabel={t('terminate_button')}
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
        <SpiffTooltip title={t('suspend_tooltip')} placement="top">
          <IconButton
            onClick={suspendProcessInstance}
            aria-label={t('suspend_tooltip')}
          >
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
        <SpiffTooltip title={t('migrate')} placement="top">
          <IconButton
            onClick={navigateToProcessInstanceMigratePage}
            aria-label={t('migrate')}
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
      <SpiffTooltip title={t('copy_shareable_link_tooltip')} placement="top">
        <IconButton
          onClick={copyProcessInstanceShortLink}
          aria-label={t('copy_shareable_link_tooltip')}
        >
          <LinkOutlined />
        </IconButton>
      </SpiffTooltip>
    );
  };

  const resumeButton = () => {
    if (processInstance && processInstance.status === 'suspended') {
      return (
        <SpiffTooltip title={t('resume')} placement="top">
          <IconButton onClick={resumeProcessInstance} aria-label={t('resume')}>
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
        <ConfirmIconButton
          data-testid="process-instance-delete"
          renderIcon={<DeleteOutlineOutlined />}
          iconDescription={t('delete')}
          description={t('delete_process_instance', { id: processInstance.id })}
          onConfirmation={deleteProcessInstance}
          confirmButtonLabel={t('delete')}
        />
      );
    }
    return null;
  };

  const initializeTaskInstancesToDisplay = useCallback(
    (task: BasicTask | null) => {
      if (!task) {
        return;
      }
      HttpService.makeCallToBackend({
        path: `/tasks/${params.process_instance_id}/${task.guid}/task-instances`,
        httpMethod: 'GET',
        // reverse operates on self as well as return the new ordered array so reverse it right away
        successCallback: (results: BasicTask[]) =>
          setTaskInstancesToDisplay(results.reverse()),
        failureCallback: (err: any) => {
          setTaskDataToDisplay(`ERROR: ${err.message}`);
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

  const handleProcessDataDisplayClose = () => {
    setProcessDataToDisplay(null);
  };

  const processDataDisplayArea = () => {
    if (processDataToDisplay) {
      let bodyComponent = (
        <>
          <p>{t('value')}:</p>
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
              t,
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
            {t('process_data_object', {
              identifier: processDataToDisplay.process_data_identifier,
            })}
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
        const matchingTask: BasicTask | undefined = tasks.find(
          (task: BasicTask) => {
            return task.bpmn_identifier === parentProcessIdentifier;
          },
        );
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
        const matchingTask: BasicTask | undefined = tasks.find(
          (task: BasicTask) => {
            return (
              task.bpmn_identifier === shapeElement.id &&
              bpmnProcessIdentifiers.includes(
                task.bpmn_process_definition_identifier,
              )
            );
          },
        );
        return matchingTask;
      }
      return undefined;
    },
    [tasks],
  );

  const handleCallActivityNavigate = useCallback(
    (task: BasicTask, event: any) => {
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
      showingActiveTask()
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
      showingActiveTask()
    );
  };

  const canCompleteTask = (task: BasicTask) => {
    return (
      processInstance &&
      processInstance.status === 'suspended' &&
      ability.can('POST', targetUris.processInstanceCompleteTaskPath) &&
      isActiveTask(task) &&
      showingActiveTask()
    );
  };

  const canAddPotentialOwners = (task: BasicTask) => {
    return (
      HUMAN_TASK_TYPES.includes(task.typename) &&
      processInstance &&
      processInstance.status === 'suspended' &&
      ability.can('POST', targetUris.processInstanceTaskAssignPath) &&
      isActiveTask(task) &&
      showingActiveTask()
    );
  };

  const canResetProcess = (task: BasicTask) => {
    return (
      ability.can('POST', targetUris.processInstanceResetPath) &&
      processInstance &&
      processInstance.status === 'suspended' &&
      task.state === 'READY' &&
      !showingActiveTask()
    );
  };

  const getEvents = (task: BasicTask) => {
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

  const taskDisplayButtons = (task: BasicTask) => {
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
          data-testid="create-script-unit-test-button"
          onClick={createScriptUnitTest}
        >
          {t('create_script_unit_test')}
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
          {t('view_call_activity_diagram')}
        </Button>,
      );
    }

    if (canEditTaskData(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Edit />}
          data-testid="edit-task-data-button"
          onClick={() => setEditingTaskData(true)}
        >
          {t('edit_task_data')}
        </Button>,
      );
    }
    if (canAddPotentialOwners(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<UserFollow />}
          title="Allow an additional user to complete this task"
          data-testid="add-potential-owners-button"
          onClick={() => setAddingPotentialOwners(true)}
        >
          {t('assign_user')}
        </Button>,
      );
    }
    if (canCompleteTask(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Play />}
          data-testid="execute-task-complete-button"
          onClick={() => completeTask(true)}
        >
          {t('execute_task')}
        </Button>,
      );
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<SkipForward />}
          data-testid="mark-task-complete-button"
          onClick={() => completeTask(false)}
        >
          {t('skip_task')}
        </Button>,
      );
    }
    if (canSendEvent(task)) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Send />}
          data-testid="select-event-button"
          onClick={() => setSelectingEvent(true)}
        >
          {t('send_event')}
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
          data-testid="reset-process-button"
          onClick={() => resetProcessInstance()}
        >
          {t('reset_process_here')}
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
    let taskDataHeader = t('task_data');
    let editorReadOnly = true;
    let taskDataHeaderClassName = 'with-half-rem-bottom-margin';

    if (editingTaskData) {
      editorReadOnly = false;
      taskDataHeader = t('edit_task_data_heading');
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
        <h3 className="task-data-details-header">
          {t('update_task_ownership')}
        </h3>
        <div className="indented-content">
          <p className="explanatory-message with-tiny-bottom-margin">
            {t('select_user_to_complete_task')}
          </p>
          {error && (
            <div style={{ color: 'red', marginBottom: '10px' }}>
              {error.message}
            </div>
          )}
          <UserSearch
            className="modal-dropdown"
            onSelectedUser={(user: User) => {
              setAdditionalPotentialOwners([user]);
              removeError();
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
        <h3 className="task-data-details-header">
          {t('choose_event_to_send')}
        </h3>
        <div className="indented-content">
          <p className="explanatory-message with-tiny-bottom-margin">
            {t('select_event_description')}
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

  const taskIsInstanceOfMultiInstanceTask = (task: BasicTask) => {
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
  const createButtonSetForTaskInstances = () => {
    if (taskInstancesToDisplay.length === 0 || !taskToDisplay) {
      return null;
    }
    return (
      <>
        {taskInstancesToDisplay.map((task: BasicTask, index: number) => {
          const buttonClass =
            task.guid === taskToDisplay.guid ? 'selected-task-instance' : null;
          return (
            <Grid container spacing={2}>
              <Grid size={{ xs: 1 }}>
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
              <Grid size={{ xs: 11 }}>
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
            {t('task_instances')} ({taskInstancesToDisplay.length})
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
              {t('mi_instances', { type: titleizeString(infoType) })} (
              {taskInstances.length})
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
        text += t('remaining', {
          count: taskToDisplay.runtime_info.iterations_remaining,
        });
      }
      accordionItems.push(
        <Accordion key="mi-loop-iterations">
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            {t('loop_iterations')} ({buttons.length})
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

    let primaryButtonText = t('close');
    let secondaryButtonText = null;
    let onRequestSubmit = handleTaskDataDisplayClose;
    let onSecondarySubmit = handleTaskDataDisplayClose;
    if (editingTaskData) {
      primaryButtonText = t('save');
      secondaryButtonText = t('cancel');
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = saveTaskData;
    } else if (selectingEvent) {
      primaryButtonText = t('send_button');
      secondaryButtonText = t('cancel');
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = sendEvent;
    } else if (addingPotentialOwners) {
      primaryButtonText = t('add_button');
      secondaryButtonText = t('cancel');
      onSecondarySubmit = resetTaskActionDetails;
      onRequestSubmit = addPotentialOwners;
    }
    if (taskToDisplay.runtime_info) {
      if (typeof taskToDisplay.runtime_info.instance !== 'undefined') {
        secondaryButtonText = t('return_to_mi_task');
        onSecondarySubmit = () => {
          switchToTask(taskToDisplay.properties_json.parent, [
            ...(tasks || []),
            ...taskInstancesToDisplay,
          ]);
        };
      } else if (typeof taskToDisplay.runtime_info.iteration !== 'undefined') {
        secondaryButtonText = t('return_to_loop_task');
        onSecondarySubmit = () => {
          switchToTask(taskToDisplay.properties_json.parent, [
            ...(tasks || []),
            ...taskInstancesToDisplay,
          ]);
        };
      }
    }

    return (
      <Dialog
        open={!!taskToDisplay}
        onClose={handleTaskDataDisplayClose}
        className="wide-dialog"
      >
        <DialogTitle>{`${taskToDisplay.bpmn_identifier} (${taskToDisplay.typename}): ${taskToDisplay.state}`}</DialogTitle>
        <DialogContent>
          <div className="indented-content explanatory-message">
            {taskToDisplay.bpmn_name ? (
              <div>
                <Box display="flex" gap={2}>
                  Name: {taskToDisplay.bpmn_name}
                </Box>
              </div>
            ) : null}

            <div>
              <Box display="flex" gap={2}>
                Guid: {taskToDisplay.guid}
              </Box>
            </div>
          </div>
          {taskDisplayButtons(taskToDisplay)}
          {taskToDisplay.state === 'COMPLETED' ||
          taskToDisplay.state === 'ERROR' ? (
            <div className="indented-content">
              <Box display="flex" gap={2}>
                {completionViewLink(
                  'View process instance at the time when this task was active.',
                  taskToDisplay.guid,
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
          title={t('copied_link_to_clipboard')}
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
          <Grid size={{ xs: 12 }}>
            <p>
              {t('viewing_process_instance_at_time_when')}{' '}
              <span title={title}>
                <strong>
                  {taskToTimeTravelTo.bpmn_name ||
                    taskToTimeTravelTo.bpmn_identifier}
                </strong>
              </span>{' '}
              {t('was_active')}.{' '}
              <Link
                reloadDocument
                data-testid="process-instance-view-active-task-link"
                to={processInstanceShowPageBaseUrl}
              >
                {t('view_current_process_instance_state')}.
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

    const hasDiagramXml = !!processInstance.bpmn_xml_file_contents;
    const canLoadFromModel =
      !!diagramFileName && !!diagramProcessModelId && !hasDiagramXml;
    const retrievalError =
      processInstance.bpmn_xml_file_contents_retrieval_error || '';
    const detailsComponent = (
      <>
        {childrenForErrorObject(
          errorForDisplayFromString(diagramLoadError || retrievalError),
          t,
        )}
      </>
    );

    if (
      !hasDiagramXml &&
      !canLoadFromModel &&
      (diagramLoadError || retrievalError)
    ) {
      return (
        <Notification
          title={t('failed_to_load_diagram')}
          type="error"
          hideCloseButton
          allowTogglingFullMessage
        >
          {detailsComponent}
        </Notification>
      );
    }

    return (
      <>
        <ReactDiagramEditor
          diagramType="readonly"
          diagramXML={processInstance.bpmn_xml_file_contents || ''}
          fileName={canLoadFromModel ? diagramFileName || undefined : undefined}
          onCallActivityOverlayClick={handleCallActivityNavigate}
          onElementClick={handleClickedDiagramTask}
          modifiedProcessModelId={
            canLoadFromModel
              ? diagramProcessModelId || ''
              : modifiedProcessModelId || ''
          }
          tasks={tasks}
        />
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
          <Tab label={t('completed_by_me_tab')} />
          <Tab label={t('all_completed_tab')} />
        </Tabs>
        <Box>
          {selectedTaskTabSubTab === 0 ? (
            <TaskListTable
              apiPath={`/tasks/completed-by-me/${processInstance.id}`}
              paginationClassName="with-large-bottom-margin"
              textToShowIfEmpty={t('no_completed_tasks_by_me')}
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
              textToShowIfEmpty={t('no_completed_tasks')}
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
          <Tab label={t('diagram_tab')} />
          <Tab label={t('milestones_tab')} disabled={!canViewLogs} />
          <Tab label={t('events_tab')} disabled={!canViewLogs} />
          <Tab label={t('messages')} disabled={!canViewMsgs} />
          <Tab label={t('tasks_tab')} />
        </Tabs>
        <Box>
          {selectedTabIndex === 0 ? diagramArea() : null}
          {selectedTabIndex === 1 ? (
            <ProcessInstanceLogList
              variant={variant}
              isEventsView={false}
              modifiedProcessModelId={modifiedProcessModelId || ''}
              processInstanceId={processInstance.id}
            />
          ) : null}
          {selectedTabIndex === 2 ? (
            <ProcessInstanceLogList
              variant={variant}
              isEventsView
              modifiedProcessModelId={modifiedProcessModelId || ''}
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
            [t('process_groups'), '/process-groups'],
            {
              entityToExplode: processModelId,
              entityType: 'process-model-id',
              linkLastItem: true,
            },
            [t('process_id_label', { id: processInstance.id })],
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
            {t('process_id_label', { id: processInstance.id })}
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
          tableTitle={t('tasks_i_can_complete')}
          tableDescription={t('tasks_i_can_complete_description')}
          paginationClassName="with-large-bottom-margin"
          textToShowIfEmpty={t('no_tasks_to_complete')}
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

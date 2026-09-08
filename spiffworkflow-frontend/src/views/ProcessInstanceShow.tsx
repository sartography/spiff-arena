import { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import {
  useParams,
  useNavigate,
  useHref,
  useSearchParams,
} from 'react-router-dom';
import { Box, Typography, CircularProgress } from '@mui/material';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import {
  modifyProcessIdentifierForPathParam,
  unModifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import {
  BasicTask,
  ErrorForDisplay,
  KeyboardShortcuts,
  PermissionsToCheck,
  ProcessData,
  ProcessInstance,
  ProcessModel,
} from '../interfaces';
import { usePermissionFetcher } from '../hooks/PermissionService';
import TaskListTable from '../components/TaskListTable';
import useAPIError from '../hooks/UseApiError';
import ProcessInstanceCurrentTaskInfo from '../components/ProcessInstanceCurrentTaskInfo';
import useKeyboardShortcut from '../hooks/useKeyboardShortcut';
import useProcessInstanceNavigate from '../hooks/useProcessInstanceNavigate';
import ProcessInstanceSummary from '../components/processInstance/ProcessInstanceSummary';
import ProcessInstanceActionBar from '../components/processInstance/ProcessInstanceActionBar';
import ProcessDataDialog from '../components/processInstance/ProcessDataDialog';
import HistoricalStateBanner from '../components/processInstance/HistoricalStateBanner';
import ProcessInstanceTabs from '../components/processInstance/ProcessInstanceTabs';
import TaskInspectorDialog from '../components/processInstance/TaskInspectorDialog';
import useTaskInspector from '../components/processInstance/useTaskInspector';

type OwnProps = {
  variant: string;
};

export default function ProcessInstanceShow({ variant }: OwnProps) {
  const navigate = useNavigate();
  const params = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const { navigateToInstance } = useProcessInstanceNavigate();

  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);
  const [tasks, setTasks] = useState<BasicTask[] | null>(null);
  const [tasksCallHadError, setTasksCallHadError] = useState<boolean>(false);
  const [taskToTimeTravelTo, setTaskToTimeTravelTo] =
    useState<BasicTask | null>(null);

  const [processDataToDisplay, setProcessDataToDisplay] =
    useState<ProcessData | null>(null);
  const [diagramFileName, setDiagramFileName] = useState<string | null>(null);
  const [diagramProcessModelId, setDiagramProcessModelId] = useState<
    string | null
  >(null);
  const [diagramLoadError, setDiagramLoadError] = useState<string | null>(null);

  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const [selectedTaskTabSubTab, setSelectedTaskTabSubTab] = useState<number>(0);
  const [copiedShortLinkToClipboard, setCopiedShortLinkToClipboard] =
    useState<boolean>(false);

  const { addError } = useAPIError();
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

  const processInstanceAllVariantHref = useHref(
    `${processInstanceShowPageBaseUrlAllVariant}${queryParams()}`,
  );
  const processInstanceHref = useHref(
    `${processInstanceShowPageBaseUrl}${queryParams()}`,
  );
  const processInstanceShortHref = useHref(
    processInstance ? `/i/${processInstance.id}` : '/',
  );

  // to force update the diagram since it could have changed
  const refreshPage = () => {
    // redirect to the all variant page if possible to avoid potential user/task association issues.
    // such as terminating a process instance with a task that the current user is assigned to which
    // will remove the task assigned to them and could potentially remove that users association to the process instance
    if (ability.can('GET', targetUris.processInstanceActionPath)) {
      window.location.href = processInstanceAllVariantHref;
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
  const returnToProcessInstance = () => {
    window.location.href = processInstanceHref;
  };
  const resetProcessInstance = (taskGuid = currentToTaskGuid()) => {
    if (!taskGuid) {
      return;
    }
    HttpService.makeCallToBackend({
      path: `${targetUris.processInstanceResetPath}/${taskGuid}`,
      successCallback: returnToProcessInstance,
      httpMethod: 'POST',
    });
  };
  const copyProcessInstanceShortLink = () => {
    if (processInstance) {
      const piShortLink = `${window.location.origin}${processInstanceShortHref}`;
      navigator.clipboard.writeText(piShortLink);
      setCopiedShortLinkToClipboard(true);
    }
  };

  const navigateToProcessInstanceMigratePage = () => {
    navigate(
      `/process-instances/${params.process_model_id}/${params.process_instance_id}/migrate`,
    );
  };

  const handleProcessDataDisplayClose = () => {
    setProcessDataToDisplay(null);
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

  const { openTaskInspector, dialogProps: taskInspectorDialogProps } =
    useTaskInspector({
      processInstanceId: params.process_instance_id,
      modifiedProcessModelId,
      tasks,
      processInstance,
      showingActiveTask: showingActiveTask(),
      ability,
      targetUris,
      completionViewBaseUrl: processInstanceShowPageBaseUrl,
      completionQueryParams: queryParams(),
      onSendEventSuccess: refreshPage,
      onCompleteTaskSuccess: returnToProcessInstance,
      onResetProcess: resetProcessInstance,
      onNavigateCallActivity: handleCallActivityNavigate,
    });

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
          openTaskInspector(matchingTask);
        }
      }
    },
    [
      findMatchingTaskFromShapeElement,
      makeProcessDataCallFromShapeElement,
      openTaskInspector,
      tasks,
    ],
  );

  const updateSelectedTab = (newTabIndex: any) => {
    // this causes the process instance and task list to render again as well
    // it'd be nice if we could find a way to avoid that
    updateSearchParams(newTabIndex, 'tab');
  };

  const updateSelectedTaskTabSubTab = (newTabIndex: any) => {
    updateSearchParams(newTabIndex, 'taskSubTab');
  };

  if (processInstance && permissionsLoaded) {
    const canViewLogs = ability.can(
      'GET',
      targetUris.processInstanceLogListPath,
    );
    const canViewMsgs = ability.can('GET', targetUris.messageInstanceListPath);

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
        <TaskInspectorDialog {...taskInspectorDialogProps} />
        <ProcessDataDialog
          processData={processDataToDisplay}
          onClose={handleProcessDataDisplayClose}
        />
        <HistoricalStateBanner
          taskToTimeTravelTo={taskToTimeTravelTo}
          processInstanceShowPageBaseUrl={processInstanceShowPageBaseUrl}
        />
        <Box display="flex" alignItems="center" gap={1}>
          <Typography
            variant="h1"
            sx={{
              mr: '1rem',
            }}
          >
            {t('process_id_label', { id: processInstance.id })}
          </Typography>
          <ProcessInstanceActionBar
            processInstance={processInstance}
            canDelete={ability.can(
              'DELETE',
              targetUris.processInstanceActionPath,
            )}
            canMigrate={ability.can(
              'POST',
              targetUris.processInstanceMigratePath,
            )}
            canResume={ability.can(
              'POST',
              targetUris.processInstanceResumePath,
            )}
            canSuspend={ability.can(
              'POST',
              targetUris.processInstanceSuspendPath,
            )}
            canTerminate={ability.can(
              'POST',
              targetUris.processInstanceTerminatePath,
            )}
            copiedShortLinkToClipboard={copiedShortLinkToClipboard}
            onCopyShortLink={copyProcessInstanceShortLink}
            onCopiedNotificationClose={() =>
              setCopiedShortLinkToClipboard(false)
            }
            onDelete={deleteProcessInstance}
            onMigrate={navigateToProcessInstanceMigratePage}
            onResume={resumeProcessInstance}
            onSuspend={suspendProcessInstance}
            onTerminate={terminateProcessInstance}
          />
        </Box>
        <ProcessInstanceSummary processInstance={processInstance} />
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
        <ProcessInstanceTabs
          processInstance={processInstance}
          variant={variant}
          modifiedProcessModelId={modifiedProcessModelId || ''}
          selectedTabIndex={selectedTabIndex}
          selectedTaskTabSubTab={selectedTaskTabSubTab}
          canViewLogs={canViewLogs}
          canViewMsgs={canViewMsgs}
          tasks={tasks}
          tasksCallHadError={tasksCallHadError}
          diagramFileName={diagramFileName}
          diagramProcessModelId={diagramProcessModelId}
          diagramLoadError={diagramLoadError}
          onSelectTab={updateSelectedTab}
          onSelectTaskSubTab={updateSelectedTaskTabSubTab}
          onCallActivityNavigate={handleCallActivityNavigate}
          onElementClick={handleClickedDiagramTask}
        />
      </>
    );
  }

  return (
    // description="Active loading indicator"
    <CircularProgress style={{ margin: '50px 0 50px 50px' }} />
  );
}

import { ReactElement } from 'react';
import { useTranslation } from 'react-i18next';
import { Link } from 'react-router-dom';
import { json } from '@codemirror/lang-json';
import { EditorState, type Extension } from '@codemirror/state';
import { EditorView } from 'codemirror';
import {
  Send,
  Edit,
  PersonAddAlt as UserFollow,
  RestartAlt as Reset,
  Rule as RuleDraft,
  SkipNext as SkipForward,
  Visibility as View,
  ExpandMore as ExpandMoreIcon,
  PlayArrow,
} from '@mui/icons-material';
import {
  Box,
  IconButton,
  Button,
  CircularProgress,
  MenuItem,
  Select,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Link as MuiLink,
} from '@mui/material';
import Grid from '@mui/material/Grid';
import ThemedCodeMirror from '../ThemedCodeMirror';
import FormattedDateTime from '../FormattedDateTime';
import SpiffTooltip from '../SpiffTooltip';
import UserSearch from '../UserSearch';
import {
  MULTI_INSTANCE_TASK_TYPES,
  LOOP_TASK_TYPES,
  titleizeString,
} from '../../helpers';
import { BasicTask, ErrorForDisplay, User } from '../../interfaces';
import TaskRetryDetails from './TaskRetryDetails';

export type TaskInspectorDialogProps = {
  taskToDisplay: BasicTask | null;
  taskDataToDisplay: string;
  taskInstancesToDisplay: BasicTask[];
  showTaskDataLoading: boolean;
  editingTaskData: boolean;
  selectingEvent: boolean;
  addingPotentialOwners: boolean;
  eventToSend: any;
  eventPayload: string;
  eventTextEditorEnabled: boolean;
  tasks: BasicTask[] | null;
  actionError: ErrorForDisplay | null;
  candidateEvents: any[];
  canCreateScriptUnitTest: boolean;
  canEditTaskData: boolean;
  canAddPotentialOwners: boolean;
  canCompleteTask: boolean;
  canSendEvent: boolean;
  canResetProcess: boolean;
  completionViewBaseUrl: string;
  completionQueryParams: string;
  onClose: () => void;
  onHideTask: () => void;
  onTaskDataChange: (value: string) => void;
  onStartEditTaskData: () => void;
  onStartAddingPotentialOwners: () => void;
  onStartSelectingEvent: () => void;
  onCancelAction: () => void;
  onSaveTaskData: () => void;
  onAddPotentialOwners: () => void;
  onSelectUser: (user: User) => void;
  onSendEvent: () => void;
  onCompleteTask: (execute: boolean) => void;
  onResetProcess: (taskGuid: string) => void;
  onCreateScriptUnitTest: () => void;
  onNavigateCallActivity: (task: BasicTask, event: any) => void;
  onEventChange: (typename: string, candidateEvents: any[]) => void;
  onEventPayloadChange: (value: any) => void;
  onSwitchTask: (taskGuid: string, taskListToUse: BasicTask[] | null) => void;
};

export default function TaskInspectorDialog(props: TaskInspectorDialogProps) {
  const {
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
    candidateEvents,
    canCreateScriptUnitTest,
    canEditTaskData,
    canAddPotentialOwners,
    canCompleteTask,
    canSendEvent,
    canResetProcess,
    completionViewBaseUrl,
    completionQueryParams,
    onClose,
    onHideTask,
    onTaskDataChange,
    onStartEditTaskData,
    onStartAddingPotentialOwners,
    onStartSelectingEvent,
    onCancelAction,
    onSaveTaskData,
    onAddPotentialOwners,
    onSelectUser,
    onSendEvent,
    onCompleteTask,
    onResetProcess,
    onCreateScriptUnitTest,
    onNavigateCallActivity,
    onEventChange,
    onEventPayloadChange,
    onSwitchTask,
  } = props;
  const { t } = useTranslation();

  if (!taskToDisplay) {
    return null;
  }
  const task = taskToDisplay;

  const completionViewLink = (label: any, taskGuid: string) => {
    return (
      <MuiLink
        component={Link}
        reloadDocument
        data-testid="process-instance-step-link"
        to={`${completionViewBaseUrl}/${taskGuid}${completionQueryParams}`}
        sx={(theme) => ({
          color:
            theme.palette.mode === 'dark'
              ? theme.palette.info.light
              : theme.palette.primary.main,
        })}
      >
        {label}
      </MuiLink>
    );
  };

  const taskDisplayButtons = () => {
    const buttons = [];
    if (editingTaskData || addingPotentialOwners || selectingEvent) {
      return null;
    }

    if (task.typename === 'ScriptTask' && canCreateScriptUnitTest) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<RuleDraft />}
          data-testid="create-script-unit-test-button"
          onClick={onCreateScriptUnitTest}
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
            onNavigateCallActivity(task, event);
          }}
          onClick={(event: any) => {
            onHideTask();
            onNavigateCallActivity(task, event);
          }}
        >
          {t('view_call_activity_diagram')}
        </Button>,
      );
    }

    if (canEditTaskData) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Edit />}
          data-testid="edit-task-data-button"
          onClick={onStartEditTaskData}
        >
          {t('edit_task_data')}
        </Button>,
      );
    }
    if (canAddPotentialOwners) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<UserFollow />}
          title="Allow an additional user to complete this task"
          data-testid="add-potential-owners-button"
          onClick={onStartAddingPotentialOwners}
        >
          {t('assign_user')}
        </Button>,
      );
    }
    if (canCompleteTask) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<PlayArrow />}
          data-testid="execute-task-complete-button"
          onClick={() => onCompleteTask(true)}
        >
          {t('execute_task')}
        </Button>,
      );
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<SkipForward />}
          data-testid="mark-task-complete-button"
          onClick={() => onCompleteTask(false)}
        >
          {t('skip_task')}
        </Button>,
      );
    }
    if (canSendEvent) {
      buttons.push(
        <Button
          variant="outlined"
          startIcon={<Send />}
          data-testid="select-event-button"
          onClick={onStartSelectingEvent}
        >
          {t('send_event')}
        </Button>,
      );
    }
    if (canResetProcess) {
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
          onClick={() => onResetProcess(task.guid)}
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
    if (heightInEm > 30) {
      heightInEm = 30;
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

    const extensions: Extension[] = [json()];
    if (editorReadOnly) {
      extensions.push(EditorState.readOnly.of(true));
      extensions.push(EditorView.editable.of(false));
      extensions.push(EditorView.contentAttributes.of({ tabindex: '0' }));
    }

    return (
      <>
        {showTaskDataLoading ? <CircularProgress size={24} /> : null}
        {taskDataClassName !== '' ? (
          <pre className={taskDataClassName}>{taskDataToDisplay}</pre>
        ) : (
          <>
            <h3 className={taskDataHeaderClassName}>{taskDataHeader}</h3>
            <ThemedCodeMirror
              height={`${heightInEm}rem`}
              value={taskDataToDisplay}
              extensions={extensions}
              onChange={(value) => {
                onTaskDataChange(value || '');
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
          {actionError && (
            <div style={{ color: 'red', marginBottom: '10px' }}>
              {actionError.message}
            </div>
          )}
          <UserSearch
            className="modal-dropdown"
            onSelectedUser={(user: User) => {
              onSelectUser(user);
            }}
          />
        </div>
      </Box>
    );
  };

  const eventSelector = () => {
    let editor = null;
    let className = 'modal-dropdown';
    if (eventTextEditorEnabled) {
      className = '';
      editor = (
        <ThemedCodeMirror
          height={'300px'}
          value={eventPayload}
          extensions={[json()]}
          onChange={(value: any) => onEventPayloadChange(value || '{}')}
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
              onEventChange(event.target.value, candidateEvents);
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

  const taskIsInstanceOfMultiInstanceTask = () => {
    // this is the same check made in the backend in the _process_instance_task_list method to determine
    // if the given task is an instance of a multi-instance or loop task.
    // we need to avoid resetting the task instance list since the list may not be the same as we need
    return 'instance' in task.runtime_info || 'iteration' in task.runtime_info;
  };

  const taskActionDetails = () => {
    let dataArea = taskDataContainer();
    if (selectingEvent) {
      dataArea = eventSelector();
    } else if (addingPotentialOwners) {
      dataArea = potentialOwnerSelector();
    }
    return dataArea;
  };

  const createButtonSetForTaskInstances = () => {
    if (taskInstancesToDisplay.length === 0) {
      return null;
    }
    return (
      <>
        {taskInstancesToDisplay.map(
          (instanceTask: BasicTask, index: number) => {
            const isSelectedTaskInstance = instanceTask.guid === task.guid;
            const buttonClass = isSelectedTaskInstance
              ? 'selected-task-instance'
              : null;
            return (
              <Grid container spacing={2} key={instanceTask.guid}>
                <Grid size={{ xs: 1 }}>
                  {isSelectedTaskInstance ? null : (
                    <SpiffTooltip title="View">
                      <IconButton
                        onClick={() =>
                          onSwitchTask(
                            instanceTask.guid,
                            taskInstancesToDisplay,
                          )
                        }
                      >
                        <View />
                      </IconButton>
                    </SpiffTooltip>
                  )}
                </Grid>
                <Grid size={{ xs: 11 }}>
                  <div
                    className={`task-instance-modal-row-item ${buttonClass}`}
                  >
                    {index + 1} {': '}
                    <FormattedDateTime
                      seconds={instanceTask.properties_json.last_state_change}
                    />{' '}
                    {' - '} {instanceTask.state}
                  </div>
                </Grid>
              </Grid>
            );
          },
        )}
      </>
    );
  };

  const createButtonsForMultiTasks = (
    instances: number[],
    infoType: string,
  ) => {
    if (!tasks) {
      return [];
    }
    return instances.map((v: any) => {
      return (
        <Button
          variant="outlined"
          key={`btn-switch-instance-${infoType}-${v}`}
          onClick={() => onSwitchTask(task.runtime_info.instance_map[v], tasks)}
        >
          {v + 1}
        </Button>
      );
    });
  };

  const taskInstanceSelector = () => {
    const accordionItems = [];

    if (
      !taskIsInstanceOfMultiInstanceTask() &&
      taskInstancesToDisplay.length > 0
    ) {
      accordionItems.push(
        <Accordion
          key="mi-task-instances"
          defaultExpanded={taskInstancesToDisplay.length <= 3}
        >
          <AccordionSummary expandIcon={<ExpandMoreIcon />}>
            {t('task_instances')} ({taskInstancesToDisplay.length})
          </AccordionSummary>
          <AccordionDetails>
            {createButtonSetForTaskInstances()}
          </AccordionDetails>
        </Accordion>,
      );
    }

    if (MULTI_INSTANCE_TASK_TYPES.includes(task.typename)) {
      ['completed', 'running', 'future'].forEach((infoType: string) => {
        let taskInstances: ReactElement[] = [];
        const infoArray = task.runtime_info[infoType];
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
    if (LOOP_TASK_TYPES.includes(task.typename)) {
      const loopTaskInstanceIndexes = [
        ...Array(task.runtime_info.iterations_completed).keys(),
      ];
      const buttons = createButtonsForMultiTasks(
        loopTaskInstanceIndexes,
        'mi-loop-iterations',
      );
      let text = '';
      if (
        typeof task.runtime_info.iterations_remaining !== 'undefined' &&
        task.state !== 'COMPLETED'
      ) {
        text += t('remaining', {
          count: task.runtime_info.iterations_remaining,
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

  let primaryButtonText = t('close');
  let secondaryButtonText = null;
  let onRequestSubmit = onClose;
  let onSecondarySubmit = onClose;
  if (editingTaskData) {
    primaryButtonText = t('save');
    secondaryButtonText = t('cancel');
    onSecondarySubmit = onCancelAction;
    onRequestSubmit = onSaveTaskData;
  } else if (selectingEvent) {
    primaryButtonText = t('send_button');
    secondaryButtonText = t('cancel');
    onSecondarySubmit = onCancelAction;
    onRequestSubmit = onSendEvent;
  } else if (addingPotentialOwners) {
    primaryButtonText = t('add_button');
    secondaryButtonText = t('cancel');
    onSecondarySubmit = onCancelAction;
    onRequestSubmit = onAddPotentialOwners;
  }
  if (task.runtime_info) {
    if (typeof task.runtime_info.instance !== 'undefined') {
      secondaryButtonText = t('return_to_mi_task');
      onSecondarySubmit = () => {
        onSwitchTask(task.properties_json.parent, [
          ...(tasks || []),
          ...taskInstancesToDisplay,
        ]);
      };
    } else if (typeof task.runtime_info.iteration !== 'undefined') {
      secondaryButtonText = t('return_to_loop_task');
      onSecondarySubmit = () => {
        onSwitchTask(task.properties_json.parent, [
          ...(tasks || []),
          ...taskInstancesToDisplay,
        ]);
      };
    }
  }

  return (
    <Dialog open={!!taskToDisplay} onClose={onClose} className="wide-dialog">
      <DialogTitle>{`${task.bpmn_identifier} (${task.typename}): ${task.state}`}</DialogTitle>
      <DialogContent>
        <div className="indented-content explanatory-message">
          {task.bpmn_name ? (
            <div>
              <Box display="flex" gap={2}>
                Name: {task.bpmn_name}
              </Box>
            </div>
          ) : null}

          <div>
            <Box display="flex" gap={2}>
              Guid: {task.guid}
            </Box>
          </div>
        </div>
        {taskDisplayButtons()}
        {task.state === 'COMPLETED' || task.state === 'ERROR' ? (
          <div className="indented-content">
            <Box display="flex" gap={2}>
              {completionViewLink(
                'View process instance at the time when this task was active.',
                task.guid,
              )}
            </Box>
            <br />
          </div>
        ) : null}
        <TaskRetryDetails task={task} />
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
}

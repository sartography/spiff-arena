import { fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { BasicTask } from '../../interfaces';
import TaskInspectorDialog, {
  TaskInspectorDialogProps,
} from './TaskInspectorDialog';

vi.mock('react-i18next', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-i18next')>();
  return {
    ...actual,
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

vi.mock('../ThemedCodeMirror', () => {
  return {
    default: ({ value }: any) => <div data-testid="code-mirror">{value}</div>,
  };
});

const testTask = (overrides: Partial<BasicTask> = {}) =>
  ({
    id: 1,
    guid: 'task-guid-1',
    process_instance_id: 10,
    bpmn_identifier: 'some_task',
    bpmn_name: 'Some Task',
    bpmn_process_direct_parent_guid: 'parent-guid',
    bpmn_process_definition_identifier: 'process_def',
    state: 'READY',
    typename: 'UserTask',
    properties_json: {
      parent: 'parent-guid',
      last_state_change: 100,
    },
    task_definition_properties_json: {
      spec: '{}',
    },
    process_model_display_name: 'Test Model',
    process_model_identifier: 'test/model',
    name_for_display: 'Some Task',
    can_complete: true,
    start_in_seconds: 100,
    end_in_seconds: 0,
    runtime_info: {},
    ...overrides,
  }) as unknown as BasicTask;

const baseProps = (): TaskInspectorDialogProps => ({
  taskToDisplay: testTask(),
  taskDataToDisplay: '{"a": 1}',
  taskInstancesToDisplay: [],
  showTaskDataLoading: false,
  editingTaskData: false,
  selectingEvent: false,
  addingPotentialOwners: false,
  eventToSend: {},
  eventPayload: '{}',
  eventTextEditorEnabled: false,
  tasks: [],
  actionError: null,
  candidateEvents: [],
  canCreateScriptUnitTest: false,
  canEditTaskData: false,
  canAddPotentialOwners: false,
  canCompleteTask: false,
  canSendEvent: false,
  canResetProcess: false,
  completionViewBaseUrl: '/process-instances/for-me/m:model/1',
  completionQueryParams: '',
  onClose: vi.fn(),
  onHideTask: vi.fn(),
  onTaskDataChange: vi.fn(),
  onStartEditTaskData: vi.fn(),
  onStartAddingPotentialOwners: vi.fn(),
  onStartSelectingEvent: vi.fn(),
  onCancelAction: vi.fn(),
  onSaveTaskData: vi.fn(),
  onAddPotentialOwners: vi.fn(),
  onSelectUser: vi.fn(),
  onSendEvent: vi.fn(),
  onCompleteTask: vi.fn(),
  onResetProcess: vi.fn(),
  onCreateScriptUnitTest: vi.fn(),
  onNavigateCallActivity: vi.fn(),
  onEventChange: vi.fn(),
  onEventPayloadChange: vi.fn(),
  onSwitchTask: vi.fn(),
});

const renderDialog = (props: TaskInspectorDialogProps) =>
  render(
    <MemoryRouter>
      <TaskInspectorDialog {...props} />
    </MemoryRouter>,
  );

describe('TaskInspectorDialog', () => {
  it('renders nothing without a task to display', () => {
    const { container } = renderDialog({ ...baseProps(), taskToDisplay: null });
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the task title, guid, and data', () => {
    renderDialog(baseProps());
    expect(screen.getByText('some_task (UserTask): READY')).toBeInTheDocument();
    expect(screen.getByText('Guid: task-guid-1')).toBeInTheDocument();
    expect(screen.getByTestId('code-mirror')).toHaveTextContent('{"a": 1}');
  });

  it('shows no action buttons without permissions', () => {
    renderDialog(baseProps());
    expect(
      screen.queryByTestId('edit-task-data-button'),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByTestId('execute-task-complete-button'),
    ).not.toBeInTheDocument();
    expect(screen.queryByTestId('select-event-button')).not.toBeInTheDocument();
    expect(
      screen.queryByTestId('reset-process-button'),
    ).not.toBeInTheDocument();
  });

  it('shows permitted action buttons and fires their handlers', () => {
    const props = {
      ...baseProps(),
      canEditTaskData: true,
      canCompleteTask: true,
      canSendEvent: true,
      canResetProcess: true,
    };
    renderDialog(props);
    fireEvent.click(screen.getByTestId('edit-task-data-button'));
    expect(props.onStartEditTaskData).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByTestId('execute-task-complete-button'));
    expect(props.onCompleteTask).toHaveBeenCalledWith(true);
    fireEvent.click(screen.getByTestId('mark-task-complete-button'));
    expect(props.onCompleteTask).toHaveBeenCalledWith(false);
    fireEvent.click(screen.getByTestId('select-event-button'));
    expect(props.onStartSelectingEvent).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByTestId('reset-process-button'));
    expect(props.onResetProcess).toHaveBeenCalledWith('task-guid-1');
  });

  it('saves edited task data with save and cancel actions', () => {
    const props = { ...baseProps(), editingTaskData: true };
    renderDialog(props);
    fireEvent.click(screen.getByText('save'));
    expect(props.onSaveTaskData).toHaveBeenCalledTimes(1);
    fireEvent.click(screen.getByText('cancel'));
    expect(props.onCancelAction).toHaveBeenCalledTimes(1);
  });

  it('links to the historical instance view for completed tasks', () => {
    renderDialog({
      ...baseProps(),
      taskToDisplay: testTask({ state: 'COMPLETED' }),
    });
    expect(screen.getByTestId('process-instance-step-link')).toHaveAttribute(
      'href',
      '/process-instances/for-me/m:model/1/task-guid-1',
    );
  });

  it('closes the dialog', () => {
    const props = baseProps();
    renderDialog(props);
    fireEvent.click(screen.getByText('close'));
    expect(props.onClose).toHaveBeenCalledTimes(1);
  });
});

import { act, renderHook } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { APIErrorContext } from '../../contexts/APIErrorContext';
import { BasicTask } from '../../interfaces';
import useTaskInspector from './useTaskInspector';

vi.mock('react-i18next', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-i18next')>();
  return {
    ...actual,
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

const { makeCallToBackend } = vi.hoisted(() => {
  return { makeCallToBackend: vi.fn() };
});

vi.mock('../../services/HttpService', () => {
  return {
    default: {
      makeCallToBackend,
    },
  };
});

const testTask = {
  guid: 'task-guid-1',
  state: 'READY',
  typename: 'UserTask',
  properties_json: { parent: 'parent-guid', last_state_change: 100 },
  task_definition_properties_json: { spec: '{}' },
  runtime_info: {},
} as unknown as BasicTask;

const targetUris = {
  processInstanceTaskDataPath: '/v1.0/task-data/1/10',
  processInstanceTaskAssignPath: '/v1.0/task-assign/1/10',
  processInstanceSendEventPath: '/v1.0/send-event/1/10',
  processInstanceCompleteTaskPath: '/v1.0/complete-task/1/10',
  processInstanceResetPath: '/v1.0/reset/1/10',
  processModelShowPath: '/v1.0/process-models/m:model',
} as any;

const ability = { can: () => true } as any;

const baseOptions = {
  processInstanceId: '10',
  modifiedProcessModelId: 'm:model',
  tasks: [testTask],
  processInstance: { id: 10, status: 'suspended' } as any,
  showingActiveTask: true,
  ability,
  targetUris,
  completionViewBaseUrl: '/process-instances/for-me/m:model/10',
  completionQueryParams: '',
  onSendEventSuccess: vi.fn(),
  onCompleteTaskSuccess: vi.fn(),
  onResetProcess: vi.fn(),
  onNavigateCallActivity: vi.fn(),
};

describe('useTaskInspector', () => {
  beforeEach(() => {
    makeCallToBackend.mockReset();
  });

  it('opens the inspector and loads task data and instances', () => {
    const { result } = renderHook(() => useTaskInspector({ ...baseOptions }));
    expect(result.current.dialogProps.taskToDisplay).toBeNull();

    act(() => {
      result.current.openTaskInspector(testTask);
    });

    expect(result.current.dialogProps.taskToDisplay).toEqual(testTask);
    const paths = makeCallToBackend.mock.calls.map((call: any) => call[0].path);
    expect(paths).toContain('/v1.0/task-data/1/10/task-guid-1');
    expect(paths).toContain('/tasks/10/task-guid-1/task-instances');
  });

  it('does not load task data for tasks without a viewable state', () => {
    const { result } = renderHook(() => useTaskInspector({ ...baseOptions }));

    act(() => {
      result.current.openTaskInspector({
        ...testTask,
        state: 'WAITING',
      });
    });

    const paths = makeCallToBackend.mock.calls.map((call: any) => call[0].path);
    expect(paths).not.toContain('/v1.0/task-data/1/10/task-guid-1');
    expect(paths).toContain('/tasks/10/task-guid-1/task-instances');
    expect(result.current.dialogProps.taskDataToDisplay).toEqual('');
  });

  it('completes the task with the execute flag', () => {
    const onCompleteTaskSuccess = vi.fn();
    const { result } = renderHook(() =>
      useTaskInspector({ ...baseOptions, onCompleteTaskSuccess }),
    );

    act(() => {
      result.current.openTaskInspector(testTask);
    });
    makeCallToBackend.mockReset();

    act(() => {
      result.current.dialogProps.onCompleteTask(true);
    });

    expect(makeCallToBackend).toHaveBeenCalledTimes(1);
    expect(makeCallToBackend.mock.calls[0][0].path).toEqual(
      '/task-complete/m:model/10/task-guid-1',
    );
    expect(makeCallToBackend.mock.calls[0][0].postBody).toEqual({
      execute: true,
    });

    act(() => {
      makeCallToBackend.mock.calls[0][0].successCallback({});
    });
    expect(onCompleteTaskSuccess).toHaveBeenCalledTimes(1);
  });

  it('surfaces invalid event payloads instead of dispatching', () => {
    const addError = vi.fn();
    const wrapper = ({ children }: any) => (
      <APIErrorContext.Provider
        value={{ error: null, addError, removeError: vi.fn() }}
      >
        {children}
      </APIErrorContext.Provider>
    );
    const eventTask = {
      ...testTask,
      task_definition_properties_json: {
        spec: '{}',
        event_definition: {
          typename: 'MessageEventDefinition',
          event_definitions: [{ typename: 'MessageEventDefinition' }],
        },
      },
    } as unknown as BasicTask;
    const { result } = renderHook(() => useTaskInspector({ ...baseOptions }), {
      wrapper,
    });

    act(() => {
      result.current.openTaskInspector(eventTask);
    });
    act(() => {
      result.current.dialogProps.onEventChange(
        'MessageEventDefinition',
        result.current.dialogProps.candidateEvents,
      );
    });
    act(() => {
      result.current.dialogProps.onEventPayloadChange('not-json');
    });
    makeCallToBackend.mockReset();

    act(() => {
      result.current.dialogProps.onSendEvent();
    });

    expect(makeCallToBackend).not.toHaveBeenCalled();
    expect(addError).toHaveBeenCalledTimes(1);
    expect(String(addError.mock.calls[0][0].message)).toMatch(/invalid json/i);
  });

  it('dispatches the event for valid event payloads', () => {
    const { result } = renderHook(() => useTaskInspector({ ...baseOptions }));
    const eventTask = {
      ...testTask,
      task_definition_properties_json: {
        spec: '{}',
        event_definition: {
          typename: 'MessageEventDefinition',
          event_definitions: [{ typename: 'MessageEventDefinition' }],
        },
      },
    } as unknown as BasicTask;

    act(() => {
      result.current.openTaskInspector(eventTask);
    });
    act(() => {
      result.current.dialogProps.onEventChange(
        'MessageEventDefinition',
        result.current.dialogProps.candidateEvents,
      );
    });
    act(() => {
      result.current.dialogProps.onEventPayloadChange('{"a": 1}');
    });
    makeCallToBackend.mockReset();

    act(() => {
      result.current.dialogProps.onSendEvent();
    });

    expect(makeCallToBackend).toHaveBeenCalledTimes(1);
    expect(makeCallToBackend.mock.calls[0][0].postBody.payload).toEqual({
      a: 1,
    });
  });

  it('requires a selected user before assigning potential owners', () => {
    const { result } = renderHook(() => useTaskInspector({ ...baseOptions }));

    act(() => {
      result.current.openTaskInspector(testTask);
    });
    makeCallToBackend.mockReset();

    act(() => {
      result.current.dialogProps.onAddPotentialOwners();
    });

    expect(makeCallToBackend).not.toHaveBeenCalled();
  });
});

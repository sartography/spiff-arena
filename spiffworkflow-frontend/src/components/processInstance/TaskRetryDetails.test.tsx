import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { BasicTask } from '../../interfaces';
import TaskRetryDetails from './TaskRetryDetails';

vi.mock('react-i18next', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-i18next')>();
  return {
    ...actual,
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

const baseTask = {
  id: 1,
  guid: 'task-guid-1',
  process_instance_id: 10,
  bpmn_identifier: 'some_task',
  bpmn_process_direct_parent_guid: 'parent-guid',
  bpmn_process_definition_identifier: 'process_def',
  state: 'WAITING',
  typename: 'ServiceTask',
  process_model_display_name: 'Test Model',
  process_model_identifier: 'test/model',
  name_for_display: 'Some Task',
  can_complete: false,
  start_in_seconds: 100,
  end_in_seconds: 0,
} as BasicTask;

const taskWithRetryInfo = (internalData: any, retries?: number) =>
  ({
    ...baseTask,
    properties_json: {
      parent: 'parent-guid',
      last_state_change: 100,
      internal_data: internalData,
    },
    task_definition_properties_json: {
      spec: '{}',
      event_definition: undefined,
      retries,
    },
  }) as unknown as BasicTask;

describe('TaskRetryDetails', () => {
  it('renders nothing when there is no retry information', () => {
    const { container } = render(
      <TaskRetryDetails task={taskWithRetryInfo({}, undefined)} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('shows configured retries and remaining retries', () => {
    render(
      <TaskRetryDetails
        task={taskWithRetryInfo({ spiff__retries_attempted: 1 }, 5)}
      />,
    );
    expect(screen.getByText('task_retry_details')).toBeInTheDocument();
    expect(screen.getByText('configured_retries:')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();
    expect(screen.getByText('retries_remaining:')).toBeInTheDocument();
    expect(screen.getByText('4')).toBeInTheDocument();
  });

  it('shows N/A remaining retries when retry counts are missing', () => {
    render(
      <TaskRetryDetails
        task={taskWithRetryInfo({ spiff__retry_at: 1700000000 }, undefined)}
      />,
    );
    expect(screen.getByText('retries_remaining:')).toBeInTheDocument();
    expect(screen.getByText('N/A')).toBeInTheDocument();
    expect(screen.getByText('next_retry_attempt:')).toBeInTheDocument();
  });
});

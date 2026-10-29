import { fireEvent, render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import HttpService from '../services/HttpService';
import TaskListTable from './TaskListTable';

vi.mock('../services/HttpService', () => ({
  default: { makeCallToBackend: vi.fn() },
}));
vi.mock('../services/UserService', () => ({
  default: {
    getPreferredUsername: () => 'participant',
    getUserEmail: () => 'participant@example.org',
  },
}));
vi.mock('./CustomForm', () => ({
  default: ({ formData }: { formData: any }) => (
    <output data-testid="form-data">{JSON.stringify(formData)}</output>
  ),
}));
vi.mock('./InstructionsForEndUser', () => ({ default: () => null }));
vi.mock('react-i18next', async (importOriginal) => ({
  ...(await importOriginal<typeof import('react-i18next')>()),
  useTranslation: () => ({ t: (key: string) => key }),
}));

const completedTask = {
  id: 'task-1',
  task_id: 'task-1',
  process_instance_id: 7,
  process_model_identifier: 'g/m',
  process_model_display_name: 'Example',
  task_name: 'Approve',
  potential_owner_usernames: 'participant',
};

function renderWithTaskData(extensions: any, data: any) {
  vi.mocked(HttpService.makeCallToBackend).mockImplementation(
    ({ path, successCallback }) => {
      if (path.startsWith('/tasks?')) {
        successCallback({
          results: [completedTask],
          pagination: { total: 1, count: 1, pages: 1 },
        });
      } else if (path.endsWith('?with_form_data=true')) {
        successCallback({
          guid: 'task-1',
          typename: 'UserTask',
          name_for_display: 'Approve',
          end_in_seconds: 1,
          form_schema: { type: 'object', properties: {} },
          extensions,
          data,
        });
      }
    },
  );
  render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <TaskListTable
          apiPath="/tasks"
          shouldPaginateTable={false}
          showProcessId={false}
          showViewFormDataButton
        />
      </MemoryRouter>
    </QueryClientProvider>,
  );
  fireEvent.click(screen.getByRole('button', { name: 'view_task' }));
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe('completed task form modal', () => {
  it('shows the form data stored under the task variableName', () => {
    renderWithTaskData(
      { variableName: 'approval' },
      { approval: { comment: 'looks good' } },
    );
    expect(screen.getByTestId('form-data').textContent).toEqual(
      '{"comment":"looks good"}',
    );
  });

  it('shows the task data when the task has no variableName', () => {
    renderWithTaskData({}, { comment: 'looks good' });
    expect(screen.getByTestId('form-data').textContent).toEqual(
      '{"comment":"looks good"}',
    );
  });

  it('scrolls forms taller than the viewport', () => {
    renderWithTaskData({}, {});
    const modalContent = screen.getByRole('heading', {
      name: 'Approve',
    }).parentElement!;
    expect(modalContent).toHaveStyle({ maxHeight: '90vh', overflowY: 'auto' });
  });
});

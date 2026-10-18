import { ReactElement } from 'react';
import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MemoryRouter, useLocation } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import HttpService from '../services/HttpService';
import TaskListTable from './TaskListTable';
import ProcessInstanceListTable from './ProcessInstanceListTable';
import TaskShow from '../views/TaskShow/TaskShow';

vi.mock('../services/HttpService', () => ({
  default: { makeCallToBackend: vi.fn() },
}));
vi.mock('../services/UserService', () => ({
  default: {
    getPreferredUsername: () => 'participant',
    getUserEmail: () => 'participant@example.org',
  },
}));
vi.mock('./CustomForm', () => ({ default: () => <div>Task form</div> }));
vi.mock('./InstructionsForEndUser', () => ({ default: () => null }));
const t = (key: string, values?: { id: number }) =>
  values?.id ? `${key} ${values.id}` : key;
vi.mock('react-i18next', async (importOriginal) => ({
  ...(await importOriginal<typeof import('react-i18next')>()),
  useTranslation: () => ({ t }),
}));

const instances = [7, 8].map((id) => ({
  id,
  process_instance_id: id,
  process_model_identifier: 'g/m',
  process_model_display_name: 'Example',
  process_instance_status: 'user_input_required',
  status: 'user_input_required',
  task_id: `task-${id}`,
  task_name: `Task ${id}`,
  potential_owner_usernames: 'participant',
  updated_at_in_seconds: 1,
  task_updated_at_in_seconds: 1,
}));
const listResponse = {
  results: instances,
  pagination: { total: 2, count: 2, pages: 1 },
  report_metadata: {
    columns: [
      'id',
      'status',
      'updated_at_in_seconds',
      'task_updated_at_in_seconds',
    ].map((accessor) => ({ accessor, Header: accessor })),
    filter_by: [],
  },
};

const permissionRequests = () =>
  vi
    .mocked(HttpService.makeCallToBackend)
    .mock.calls.map(([request]) => request)
    .filter((request) => request.path === '/permissions-check');

function respondToPermissions() {
  act(() => {
    permissionRequests().forEach(({ postBody, successCallback }) => {
      successCallback({
        results: Object.fromEntries(
          Object.keys(postBody.requests_to_check).map((path) => [
            path,
            { GET: path.endsWith('/7') },
          ]),
        ),
      });
    });
  });
}

function Location() {
  return <output data-testid="location">{useLocation().pathname}</output>;
}

function renderPage(element: ReactElement) {
  return render(
    <QueryClientProvider client={new QueryClient()}>
      <MemoryRouter>
        <Location />
        {element}
      </MemoryRouter>
    </QueryClientProvider>,
  );
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(HttpService.makeCallToBackend).mockImplementation(
    ({ path, successCallback }) => {
      if (path.startsWith('/tasks?') || path.startsWith('/process-instances')) {
        successCallback(listResponse);
      }
    },
  );
});

describe('instance links in participant navigation', () => {
  it('keeps task actions but only links permitted instance IDs', async () => {
    renderPage(<TaskListTable apiPath="/tasks" shouldPaginateTable={false} />);
    expect(screen.queryByTestId('process-instance-show-link-id')).toBeNull();
    expect(screen.getAllByRole('link', { name: 'go' })).toHaveLength(2);
    respondToPermissions();
    const link = await screen.findByTestId('process-instance-show-link-id');
    expect(link).toHaveAttribute('href', '/process-instances/for-me/g:m/7');
    expect(screen.getByText('8').closest('a')).toBeNull();
    expect(permissionRequests()).toHaveLength(1);
  });

  it.each(['for-me', 'all'])(
    'only enables permitted %s instance rows and open buttons',
    async (variant) => {
      renderPage(
        <ProcessInstanceListTable variant={variant} showActionsColumn />,
      );
      const deniedRow = screen.getByText('8').closest('tr')!;
      const allowedRow = screen.getByText('7').closest('tr')!;
      expect(
        screen.queryByRole('link', { name: 'open_process_instance' }),
      ).toBeNull();
      fireEvent.click(screen.getByText('7'));
      expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/);
      respondToPermissions();
      const prefix = variant === 'all' ? '' : '/for-me';
      const url = `/process-instances${prefix}/g:m/7`;
      const openLink = await screen.findByRole('link', {
        name: 'open_process_instance',
      });
      expect(openLink).toHaveAttribute('href', url);
      expect(allowedRow).toHaveStyle({ cursor: 'pointer' });
      expect(deniedRow).toHaveStyle({ cursor: 'default' });
      expect(
        within(deniedRow).getByRole('link', { name: 'go' }),
      ).toHaveAttribute('href', '/tasks/8/task-8');
      within(deniedRow)
        .getAllByRole('cell')
        .forEach((cell) => {
          fireEvent.click(cell);
          fireEvent.keyDown(cell, { key: 'Enter' });
        });
      expect(screen.getByTestId('location')).toHaveTextContent(/^\/$/);
      fireEvent.click(screen.getByText('7'));
      expect(screen.getByTestId('location')).toHaveTextContent(url);
    },
  );

  it.each([7, 8])(
    'permission-checks the task breadcrumb for instance %s without blocking the form',
    async (id) => {
      vi.mocked(HttpService.makeCallToBackend).mockImplementation(
        ({ path, successCallback }) => {
          if (path.startsWith('/tasks/')) {
            successCallback({
              ...instances[id === 7 ? 0 : 1],
              can_complete: true,
              name_for_display: 'My task',
              state: 'READY',
              typename: 'UserTask',
              extensions: {},
              data: {},
              form_ui_schema: {},
              signal_buttons: [],
            });
          }
        },
      );
      renderPage(<TaskShow />);
      expect(screen.getAllByText('Task form')).toHaveLength(2);
      const label = `process_id_label ${id}`;
      expect(screen.getByText(label).closest('a')).toBeNull();
      respondToPermissions();
      await waitFor(() => {
        if (id === 7) {
          expect(screen.getByRole('link', { name: label })).toHaveAttribute(
            'href',
            '/process-instances/for-me/g:m/7',
          );
        } else {
          expect(screen.queryByRole('link', { name: label })).toBeNull();
        }
      });
      expect(screen.getAllByText('Task form')).toHaveLength(2);
    },
  );
});

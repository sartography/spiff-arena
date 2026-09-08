import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { BasicTask } from '../../interfaces';
import HistoricalStateBanner from './HistoricalStateBanner';

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

const timeTravelTask = {
  id: 7,
  guid: 'time-travel-guid',
  bpmn_identifier: 'old_task',
  bpmn_name: 'Old Task',
} as BasicTask;

describe('HistoricalStateBanner', () => {
  it('renders nothing without a time travel task', () => {
    const { container } = render(
      <MemoryRouter>
        <HistoricalStateBanner
          taskToTimeTravelTo={null}
          processInstanceShowPageBaseUrl="/process-instances/for-me/m:model/1"
        />
      </MemoryRouter>,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('links back to the current instance state with the router basename', () => {
    render(
      <MemoryRouter
        basename="/workflow"
        initialEntries={['/workflow/process-instances/for-me/m:model/1/abc']}
      >
        <HistoricalStateBanner
          taskToTimeTravelTo={timeTravelTask}
          processInstanceShowPageBaseUrl="/process-instances/for-me/m:model/1"
        />
      </MemoryRouter>,
    );
    expect(screen.getByText('Old Task')).toBeInTheDocument();
    expect(
      screen.getByTestId('process-instance-view-active-task-link'),
    ).toHaveAttribute('href', '/workflow/process-instances/for-me/m:model/1');
  });
});

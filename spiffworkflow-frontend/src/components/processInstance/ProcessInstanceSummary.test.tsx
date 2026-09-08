import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, expect, it, vi } from 'vitest';
import { ProcessInstance } from '../../interfaces';
import ProcessInstanceSummary from './ProcessInstanceSummary';

vi.mock('react-i18next', async (importOriginal) => {
  const actual = await importOriginal<typeof import('react-i18next')>();
  return {
    ...actual,
    useTranslation: () => ({
      t: (value: string) => value,
    }),
  };
});

const baseInstance = {
  id: 42,
  bpmn_version_control_identifier: 'v1',
  bpmn_version_control_type: 'git',
  created_at_in_seconds: 100,
  end_in_seconds: null,
  process_initiator_username: 'some-user',
  process_metadata: [
    { key: 'order_id', value: '123' },
    { key: 'docs', value: 'https://example.com/docs' },
  ],
  process_model_display_name: 'Test Model',
  process_model_identifier: 'test/model',
  process_model_with_diagram_identifier: 'test:model',
  start_in_seconds: 100,
  status: 'suspended',
  updated_at_in_seconds: 200,
  task_updated_at_in_seconds: 200,
} as ProcessInstance;

const renderSummary = (processInstance: ProcessInstance) =>
  render(
    <MemoryRouter basename="/workflow" initialEntries={['/workflow/']}>
      <ProcessInstanceSummary processInstance={processInstance} />
    </MemoryRouter>,
  );

describe('ProcessInstanceSummary', () => {
  it('renders status, initiator, and metadata values', () => {
    renderSummary(baseInstance);
    expect(
      screen.getByTestId('process-instance-status-chip'),
    ).toBeInTheDocument();
    expect(screen.getByText('some-user')).toBeInTheDocument();
    expect(screen.getByTestId('metadata-value-order_id')).toHaveTextContent(
      '123',
    );
  });

  it('renders URL metadata as an external link', () => {
    renderSummary(baseInstance);
    const docsLink = screen.getByRole('link', { name: 'docs link' });
    expect(docsLink).toHaveAttribute('href', 'https://example.com/docs');
    expect(docsLink).toHaveAttribute('target', '_blank');
  });

  it('links to the current diagram model with the router basename', () => {
    renderSummary(baseInstance);
    expect(
      screen.getByTestId('go-to-current-diagram-process-model'),
    ).toHaveAttribute('href', '/workflow/process-models/test:model');
  });
});

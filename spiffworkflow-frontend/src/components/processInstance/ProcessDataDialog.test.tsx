import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import ProcessDataDialog from './ProcessDataDialog';

vi.mock('react-i18next', () => {
  return {
    useTranslation: () => ({
      t: (value: string, options?: any) =>
        options?.identifier ? `${value}:${options.identifier}` : value,
    }),
  };
});

describe('ProcessDataDialog', () => {
  it('renders nothing without process data', () => {
    const { container } = render(
      <ProcessDataDialog processData={null} onClose={() => undefined} />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it('renders the process data value', () => {
    render(
      <ProcessDataDialog
        processData={{
          process_data_identifier: 'order',
          process_data_value: { total: 5 },
        }}
        onClose={() => undefined}
      />,
    );
    expect(screen.getByText('process_data_object:order')).toBeInTheDocument();
    expect(screen.getByText('value:')).toBeInTheDocument();
  });
});

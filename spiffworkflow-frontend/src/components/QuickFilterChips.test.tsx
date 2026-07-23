import { fireEvent, render, screen } from '@testing-library/react';
import { expect, test, vi } from 'vitest';
import { ReportFilter, ReportMetadata } from '../interfaces';
import QuickFilterChips from './QuickFilterChips';

const t = (key: string) => key;

vi.mock('react-i18next', () => ({
  useTranslation: () => ({ t }),
}));

const metadataWithFilters = (filterBy: ReportFilter[]): ReportMetadata => ({
  columns: [],
  filter_by: filterBy,
  order_by: [],
});

test('does not infer completed quick filter active from manual status filter', () => {
  const onApplyPreset = vi.fn();
  render(
    <QuickFilterChips
      activePresetIds={[]}
      reportMetadata={metadataWithFilters([
        {
          field_name: 'process_status',
          field_value: 'complete',
          operator: 'equals',
        },
      ])}
      onApplyPreset={onApplyPreset}
    />,
  );

  fireEvent.click(screen.getByText('quick_filter_completed'));

  expect(onApplyPreset).toHaveBeenLastCalledWith(
    [
      {
        field_name: 'process_status',
        field_value: 'complete',
        operator: 'equals',
      },
    ],
    ['process_status'],
    'completed',
    false,
  );
});

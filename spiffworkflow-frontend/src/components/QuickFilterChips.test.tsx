import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
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

afterEach(() => {
  vi.useRealTimers();
});

test('keeps the last 7 days quick filter active after time advances', () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-07-01T12:00:00Z'));

  const onApplyPreset = vi.fn();
  const { rerender } = render(
    <QuickFilterChips
      reportMetadata={metadataWithFilters([])}
      onApplyPreset={onApplyPreset}
    />,
  );

  fireEvent.click(screen.getByText('quick_filter_last_7_days'));
  const selectedFilters = onApplyPreset.mock.calls[0][0];

  vi.setSystemTime(new Date('2026-07-01T12:00:05Z'));
  rerender(
    <QuickFilterChips
      reportMetadata={metadataWithFilters(selectedFilters)}
      onApplyPreset={onApplyPreset}
    />,
  );
  fireEvent.click(screen.getByText('quick_filter_last_7_days'));

  expect(onApplyPreset).toHaveBeenLastCalledWith(
    [],
    ['start_from'],
    'last_7_days',
    true,
  );
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

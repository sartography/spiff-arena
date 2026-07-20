import { fireEvent, render, screen } from '@testing-library/react';
import { afterEach, expect, test, vi } from 'vitest';
import TimeRangeFilter, {
  dateAndTimeToTimestamp,
  getTimeInputPreferences,
  parseRelativeTimeRange,
} from './TimeRangeFilter';

const TIME_RANGE_BUTTON_TEST_ID = 'time-range-filter-button';

afterEach(() => {
  vi.useRealTimers();
});

test('parses supported custom relative ranges', () => {
  expect(parseRelativeTimeRange('10m', 1_000_000)).toEqual({
    startTimestamp: 999400,
    endTimestamp: 1_000_000,
    shortLabel: '10M',
  });
  expect(parseRelativeTimeRange('2h', 1_000_000)).toEqual({
    startTimestamp: 992800,
    endTimestamp: 1_000_000,
    shortLabel: '2H',
  });
  expect(parseRelativeTimeRange('4D', 1_000_000)?.startTimestamp).toBe(654400);
  expect(parseRelativeTimeRange('8w', 10_000_000)?.startTimestamp).toBe(
    5161600,
  );
  expect(parseRelativeTimeRange('tomorrow')).toBeNull();
});

test('converts absolute UTC dates and times to timestamps', () => {
  expect(dateAndTimeToTimestamp(new Date(2026, 6, 2), '13:45', true)).toBe(
    Date.UTC(2026, 6, 2, 13, 45) / 1000,
  );
});

test('detects the locale hour cycle for native time inputs', () => {
  expect(getTimeInputPreferences('en-US').uses24HourClock).toBe(false);
  expect(getTimeInputPreferences('en-GB').uses24HourClock).toBe(true);
});

test('applies a relative preset and displays its short label', () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-07-20T12:00:00Z'));
  const onApply = vi.fn();
  render(<TimeRangeFilter onApply={onApply} />);

  fireEvent.click(screen.getByTestId(TIME_RANGE_BUTTON_TEST_ID));
  fireEvent.click(screen.getByText('Last 14 days'));

  const end = Date.parse('2026-07-20T12:00:00Z') / 1000;
  expect(onApply).toHaveBeenCalledWith(end - 14 * 86400, end);
  expect(screen.getByTestId(TIME_RANGE_BUTTON_TEST_ID)).toHaveTextContent(
    '14D',
  );
});

test('accepts a custom relative range on Enter', () => {
  vi.useFakeTimers();
  vi.setSystemTime(new Date('2026-07-20T12:00:00Z'));
  const onApply = vi.fn();
  render(<TimeRangeFilter onApply={onApply} />);

  fireEvent.click(screen.getByTestId(TIME_RANGE_BUTTON_TEST_ID));
  const input = screen.getByLabelText('Custom time range');
  fireEvent.change(input, { target: { value: '8w' } });
  fireEvent.keyDown(input, { key: 'Enter' });

  const end = Date.parse('2026-07-20T12:00:00Z') / 1000;
  expect(onApply).toHaveBeenCalledWith(end - 8 * 7 * 86400, end);
  expect(screen.getByTestId(TIME_RANGE_BUTTON_TEST_ID)).toHaveTextContent('8W');
});

test('opens the absolute date range picker and can go back', () => {
  render(<TimeRangeFilter onApply={vi.fn()} />);
  fireEvent.click(screen.getByTestId(TIME_RANGE_BUTTON_TEST_ID));
  fireEvent.click(screen.getByText('Absolute date'));

  expect(screen.getByTestId('absolute-time-range-picker')).toBeVisible();
  expect(screen.getByLabelText('Start time')).toBeVisible();
  expect(screen.getByLabelText('End time')).toBeVisible();
  expect(screen.getByLabelText('UTC')).toBeChecked();
  expect(screen.getByLabelText('Start time')).toHaveAttribute(
    'data-hour-cycle',
  );

  fireEvent.click(screen.getByText('← Back'));
  expect(
    screen.getByPlaceholderText('Custom range: 10m, 2h, 4d...'),
  ).toBeVisible();
});

test('rejects invalid absolute times', () => {
  const onApply = vi.fn();
  render(<TimeRangeFilter onApply={onApply} />);
  fireEvent.click(screen.getByTestId(TIME_RANGE_BUTTON_TEST_ID));
  fireEvent.click(screen.getByText('Absolute date'));

  fireEvent.change(screen.getByLabelText('Start time'), {
    target: { value: '' },
  });
  fireEvent.click(screen.getByText('Apply'));

  expect(screen.getByText('Enter valid start and end times.')).toBeVisible();
  expect(onApply).not.toHaveBeenCalled();
});

test('surfaces a reversed absolute range and still applies a valid range', () => {
  const onApply = vi.fn();
  render(<TimeRangeFilter onApply={onApply} />);
  fireEvent.click(screen.getByTestId(TIME_RANGE_BUTTON_TEST_ID));
  fireEvent.click(screen.getByText('Absolute date'));

  fireEvent.change(screen.getByLabelText('Start time'), {
    target: { value: '23:00' },
  });
  fireEvent.change(screen.getByLabelText('End time'), {
    target: { value: '01:00' },
  });
  fireEvent.click(screen.getByText('Apply'));

  expect(
    screen.getByText('Start date and time must be before end date and time.'),
  ).toBeVisible();
  expect(onApply).not.toHaveBeenCalled();

  fireEvent.change(screen.getByLabelText('End time'), {
    target: { value: '23:59' },
  });
  fireEvent.click(screen.getByText('Apply'));
  expect(onApply).toHaveBeenCalledOnce();
});

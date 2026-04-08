import { vi } from 'vitest';
import FormattingService from './FormattingService';
import { TimeAgo } from '../helpers/timeago';

test('it can convert date string to date for display', () => {
  const markdown =
    'HEY SPIFF_FORMAT:::convert_date_to_date_for_display(2024-03-01)';
  expect(FormattingService.checkForSpiffFormats(markdown)).toEqual(
    'HEY 2024-03-01',
  );
});

test('it can convert seconds to duration time for display', () => {
  const markdown =
    'HEY SPIFF_FORMAT:::convert_seconds_to_duration_for_display(10000)';
  expect(FormattingService.checkForSpiffFormats(markdown)).toEqual(
    'HEY 2h 46m 40s',
  );
});

test('it coerces seconds to a number before converting to time ago', () => {
  const inWordsSpy = vi
    .spyOn(TimeAgo, 'inWords')
    .mockReturnValue('moments ago');

  const markdown =
    'HEY SPIFF_FORMAT:::convert_seconds_to_time_ago_for_display(10000)';

  expect(FormattingService.checkForSpiffFormats(markdown)).toEqual(
    'HEY moments ago',
  );
  expect(inWordsSpy).toHaveBeenCalledWith(10000);

  inWordsSpy.mockRestore();
});

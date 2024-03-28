import DateAndTimeService from './DateAndTimeService';

test('it can keep the correct date when converting seconds to date', () => {
  const dateString =
    DateAndTimeService.convertSecondsToFormattedDateString(1666325400);
  expect(dateString).toEqual('2022-10-21');
});
test('it can properly format a duration', () => {
  expect(DateAndTimeService.formatDurationForDisplay('0')).toEqual('0s');
  expect(DateAndTimeService.formatDurationForDisplay('60')).toEqual('1m');
  expect(DateAndTimeService.formatDurationForDisplay('65')).toEqual('1m 5s');
  expect(DateAndTimeService.formatDurationForDisplay(65)).toEqual('1m 5s');
  expect(DateAndTimeService.formatDurationForDisplay(86500)).toEqual(
    '1d 1m 40s'
  );
  expect(DateAndTimeService.formatDurationForDisplay(2629746)).toEqual(
    '30d 10h 29m 6s'
  );
  expect(DateAndTimeService.formatDurationForDisplay(31536765)).toEqual(
    '365d 12m 45s'
  );
});

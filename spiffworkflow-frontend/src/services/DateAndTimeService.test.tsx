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
    '1d 1m 40s',
  );
  expect(DateAndTimeService.formatDurationForDisplay(2629746)).toEqual(
    '30d 10h 29m 6s',
  );
  expect(DateAndTimeService.formatDurationForDisplay(31536765)).toEqual(
    '365d 12m 45s',
  );
});

test('it can get the correct date format from string', () => {
  const expectedDateString = '2024-03-04';
  const newDateFormat = 'dd-MMM-yyyy';

  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      expectedDateString,
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '03-04-2024',
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      'March 4, 2024',
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      'mar-4-2024',
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '03/04/2024',
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '03.04.2024',
    ),
  ).toEqual(expectedDateString);

  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '04-03-2024',
      newDateFormat,
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      'March 4, 2024',
      newDateFormat,
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '4-mar-2024',
      newDateFormat,
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '4 March 2024',
      newDateFormat,
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '04/03/2024',
      newDateFormat,
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      '04.03.2024',
      newDateFormat,
    ),
  ).toEqual(expectedDateString);
  expect(
    DateAndTimeService.attemptToConvertUnknownDateStringFormatToKnownFormat(
      expectedDateString,
      newDateFormat,
    ),
  ).toEqual(expectedDateString);
});

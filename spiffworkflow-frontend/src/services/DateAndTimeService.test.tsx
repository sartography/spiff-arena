import DateAndTimeService from './DateAndTimeService';

test('it can tell if a string looks like a date', () => {
  const validDates = [
    '2024-06-01',
    '14-06-2024',
    '1-06-2024',
    '14-6-2024',
    '14-Jun-2024',
    '14-March-2024',
    'March 4, 2024',
    '4 March 2024',
    '04/03/2024',
    '04.03.2024',
  ];
  validDates.forEach((dateString: string) => {
    try {
      expect(DateAndTimeService.stringLooksLikeADate(dateString)).toBe(true);
    } catch (exception) {
      throw Error(`Date failed: ${dateString}: ${exception}`);
    }
  });

  const invalidDates = [
    '2024-06-0',
    '2024-6-01',
    '14-06-202',
    '14-Jun-202',
    '14#06#20204',
  ];
  invalidDates.forEach((dateString: string) => {
    try {
      expect(DateAndTimeService.stringLooksLikeADate(dateString)).toBe(false);
    } catch (exception) {
      throw Error(`Date failed: ${dateString}: ${exception}`);
    }
  });
});

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
  const marchDate = 'March 4, 2024';

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
      marchDate,
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
      marchDate,
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

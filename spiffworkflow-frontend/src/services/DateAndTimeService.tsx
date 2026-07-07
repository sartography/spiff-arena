import { Duration, format, parse } from 'date-fns';
import {
  DATE_TIME_FORMAT,
  DATE_FORMAT,
  TIME_FORMAT_HOURS_MINUTES,
} from '../config';
import { isANumber } from '../helpers';

const MINUTES_IN_HOUR = 60;
const SECONDS_IN_MINUTE = 60;
const SECONDS_IN_HOUR = MINUTES_IN_HOUR * SECONDS_IN_MINUTE;
const FOUR_HOURS_IN_SECONDS = SECONDS_IN_HOUR * 4;

const REFRESH_INTERVAL_SECONDS = 5;
const REFRESH_TIMEOUT_SECONDS = FOUR_HOURS_IN_SECONDS;

const stringLooksLikeADate = (dateString: string): boolean => {
  // We had been useing date-fns parse to really check if a date is valid however it attempts to parse dates like 14-06-2 because it thinks it is 14-06-0002.
  // This results in a validate date but has a negative time with getTime which is a valid number however we do not want dates like this at all.
  // Checking for negative numbers seem wrong so use a regex to see if it looks anything like a date.
  return (
    (dateString.match(/^\d{4}[-/.]\d{2}[-/.]\d{2}$/) ||
      dateString.match(/^(\d{1,2}|\w+)[-/.](\d{1,2}|\w+)[-/.]\d{4}$/) ||
      dateString.match(/^\w+ +\d+, +\d{4}$/) ||
      dateString.match(/^\d+ +\w+ +\d{4}$/)) !== null
  );
};

const convertDateToSeconds = (date: any, onChangeFunction: any = null) => {
  let dateInSeconds = date;
  if (date !== null) {
    let dateInMilliseconds = date;
    if (typeof date.getTime === 'function') {
      dateInMilliseconds = date.getTime();
    }
    dateInSeconds = Math.floor(dateInMilliseconds / 1000);
  }

  if (onChangeFunction) {
    onChangeFunction(dateInSeconds);
  } else {
    return dateInSeconds;
  }

  return null;
};

const convertDateObjectToFormattedString = (dateObject: Date) => {
  if (dateObject) {
    return format(dateObject, DATE_FORMAT);
  }
  return null;
};

const dateStringToYMDFormat = (dateString: string) => {
  if (dateString === undefined || dateString === null) {
    return dateString;
  }

  if (
    dateString.match(/^\d{4}-\d{2}-\d{2}$/) ||
    !stringLooksLikeADate(dateString)
  ) {
    return dateString;
  }
  const newDate = parse(dateString, DATE_FORMAT, new Date());
  // getTime returns NaN if the date is invalid
  if (Number.isNaN(newDate.getTime())) {
    return dateString;
  }
  return format(newDate, 'yyyy-MM-dd');
};

const convertDateAndTimeStringsToDate = (
  dateString: string,
  timeString: string,
) => {
  if (dateString && timeString) {
    return new Date(`${dateStringToYMDFormat(dateString)}T${timeString}`);
  }
  return null;
};

const convertDateAndTimeStringsToSeconds = (
  dateString: string,
  timeString: string,
) => {
  const dateObject = convertDateAndTimeStringsToDate(dateString, timeString);
  if (dateObject) {
    return convertDateToSeconds(dateObject);
  }
  return null;
};

const convertStringToDate = (dateString: string) => {
  return convertDateAndTimeStringsToDate(dateString, '00:10:00');
};

const ymdDateStringToConfiguredFormat = (dateString: string) => {
  const dateObject = convertStringToDate(dateString);
  if (dateObject) {
    return convertDateObjectToFormattedString(dateObject);
  }
  return null;
};

const convertSecondsToDateObject = (seconds: number) => {
  if (seconds) {
    return new Date(seconds * 1000);
  }
  return null;
};

const convertSecondsToFormattedDateTime = (seconds: number) => {
  const dateObject = convertSecondsToDateObject(seconds);
  if (dateObject) {
    return format(dateObject, DATE_TIME_FORMAT);
  }
  return null;
};

const convertDateObjectToFormattedHoursMinutes = (dateObject: Date) => {
  if (dateObject) {
    return format(dateObject, TIME_FORMAT_HOURS_MINUTES);
  }
  return null;
};

const convertSecondsToFormattedTimeHoursMinutes = (seconds: number) => {
  const dateObject = convertSecondsToDateObject(seconds);
  if (dateObject) {
    return convertDateObjectToFormattedHoursMinutes(dateObject);
  }
  return null;
};

const convertSecondsToFormattedDateString = (seconds: number) => {
  const dateObject = convertSecondsToDateObject(seconds);
  if (dateObject) {
    return convertDateObjectToFormattedString(dateObject);
  }
  return null;
};

const convertDateStringToSeconds = (dateString: string) => {
  const dateObject = convertStringToDate(dateString);
  if (dateObject) {
    return convertDateToSeconds(dateObject);
  }
  return null;
};

// logic from https://stackoverflow.com/a/28510323/6090676
const secondsToDuration = (secNum: number) => {
  const days = Math.floor(secNum / 86400);
  const hours = Math.floor(secNum / 3600) % 24;
  const minutes = Math.floor(secNum / 60) % 60;
  const seconds = secNum % 60;

  const duration: Duration = {
    days,
    hours,
    minutes,
    seconds,
  };
  return duration;
};

const attemptToConvertUnknownDateStringFormatToKnownFormat = (
  dateString: string,
  targetDateFormat?: string,
) => {
  let dateFormat = targetDateFormat;
  if (!dateFormat) {
    dateFormat = DATE_FORMAT;
  }
  let newDateString = dateString;
  // if the date starts with 4 digits then assume in y-m-d format and avoid all of this
  if (stringLooksLikeADate(dateString) && !dateString.match(/^\d{4}/)) {
    // if the date format should contain month names or abbreviations but does not have letters
    // then attempt to parse in the same format but with digit months instead of letters

    if (!dateString.match(/[a-zA-Z]+/) && dateFormat.match(/MMM/)) {
      const numericalDateFormat = dateFormat.replaceAll(/MMM*/g, 'MM');
      const dateFormatRegex = new RegExp(
        numericalDateFormat
          .replace('dd', '\\d{2}')
          .replace('MM', '\\d{2}')
          .replace('yyyy', '\\d{4}'),
      );
      const normalizedDateString = dateString.replaceAll(/[.-/]+/g, '-');
      if (normalizedDateString.match(dateFormatRegex)) {
        const newDate = parse(
          normalizedDateString,
          numericalDateFormat,
          new Date(),
        );
        newDateString = convertDateObjectToFormattedString(newDate) || '';
      }
    } else {
      // NOTE: do not run Date.parse with y-m-d formats since it returns dates in a different timezone from other formats
      const newDate = new Date(Date.parse(`${dateString}`));
      newDateString = convertDateObjectToFormattedString(newDate) || '';
    }
  }
  return newDateString;
};

const formatDurationForDisplay = (value: any) => {
  if (value === undefined) {
    return undefined;
  }
  const duration = secondsToDuration(parseInt(value, 10));
  const durationTimes = [];
  if (duration.seconds !== undefined && duration.seconds > 0) {
    durationTimes.unshift(`${duration.seconds}s`);
  }
  if (duration.minutes !== undefined && duration.minutes > 0) {
    durationTimes.unshift(`${duration.minutes}m`);
  }
  if (duration.hours !== undefined && duration.hours > 0) {
    durationTimes.unshift(`${duration.hours}h`);
  }
  if (duration.days !== undefined && duration.days > 0) {
    durationTimes.unshift(`${duration.days}d`);
  }
  if (durationTimes.length < 1) {
    durationTimes.push('0s');
  }
  return durationTimes.join(' ');
};

const formatDateTime = (value: any) => {
  if (value === undefined || value === null) {
    return value;
  }
  let dateInSeconds = value;
  if (!isANumber(value)) {
    const timeArgs = value.split('T');
    dateInSeconds = convertDateAndTimeStringsToSeconds(
      timeArgs[0],
      timeArgs[1],
    );
  }
  if (dateInSeconds) {
    return convertSecondsToFormattedDateTime(dateInSeconds);
  }
  return null;
};

const DateAndTimeService = {
  REFRESH_INTERVAL_SECONDS,
  REFRESH_TIMEOUT_SECONDS,

  attemptToConvertUnknownDateStringFormatToKnownFormat,
  convertDateAndTimeStringsToDate,
  convertDateAndTimeStringsToSeconds,
  convertDateObjectToFormattedHoursMinutes,
  convertDateObjectToFormattedString,
  convertDateStringToSeconds,
  convertDateToSeconds,
  convertSecondsToDateObject,
  convertSecondsToFormattedDateString,
  convertSecondsToFormattedDateTime,
  convertSecondsToFormattedTimeHoursMinutes,
  convertStringToDate,
  dateStringToYMDFormat,
  formatDateTime,
  formatDurationForDisplay,
  secondsToDuration,
  stringLooksLikeADate,
  ymdDateStringToConfiguredFormat,
};

export default DateAndTimeService;

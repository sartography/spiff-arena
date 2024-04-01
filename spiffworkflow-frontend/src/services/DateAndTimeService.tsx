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
  if (dateString && dateString.match(/^\d{4}-\d{2}-\d{2}$/)) {
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
  timeString: string
) => {
  if (dateString && timeString) {
    return new Date(`${dateStringToYMDFormat(dateString)}T${timeString}`);
  }
  return null;
};

const convertDateAndTimeStringsToSeconds = (
  dateString: string,
  timeString: string
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
      timeArgs[1]
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
  ymdDateStringToConfiguredFormat,
};

export default DateAndTimeService;

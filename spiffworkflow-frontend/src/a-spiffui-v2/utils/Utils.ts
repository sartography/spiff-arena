import DateAndTimeService from '../../services/DateAndTimeService';

/** Give a home to useful spot and general utilities */
export const formatSecondsForDisplay = (seconds: any) => {
  return DateAndTimeService.convertSecondsToFormattedDateTime(seconds) || '-';
};

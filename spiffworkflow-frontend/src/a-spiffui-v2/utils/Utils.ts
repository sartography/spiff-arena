import DateAndTimeService from '../../services/DateAndTimeService';

export const formatSecondsForDisplay = (seconds: any) => {
  return DateAndTimeService.convertSecondsToFormattedDateTime(seconds) || '-';
};

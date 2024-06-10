import DateAndTimeService from './DateAndTimeService';

const spiffFormatFunctions: { [key: string]: Function } = {
  convert_seconds_to_date_time_for_display: DateAndTimeService.formatDateTime,
  convert_seconds_to_duration_for_display:
    DateAndTimeService.formatDurationForDisplay,
  convert_date_to_date_for_display:
    DateAndTimeService.ymdDateStringToConfiguredFormat,
};

const checkForSpiffFormats = (markdown: string) => {
  const replacer = (
    match: string,
    spiffFormat: string,
    originalValue: string,
  ) => {
    if (spiffFormat in spiffFormatFunctions) {
      return spiffFormatFunctions[spiffFormat](originalValue);
    }
    console.warn(
      `attempted: ${match}, but ${spiffFormat} is not a valid conversion function`,
    );

    return match;
  };
  return markdown.replaceAll(/SPIFF_FORMAT:::(\w+)\(([^)]+)\)/g, replacer);
};

const FormattingService = {
  checkForSpiffFormats,
};

export default FormattingService;

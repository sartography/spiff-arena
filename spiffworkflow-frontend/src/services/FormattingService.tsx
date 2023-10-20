import { formatDateTime, formatDurationForDisplay } from '../helpers';

const spiffFormatFunctions: { [key: string]: Function } = {
  convert_seconds_to_date_time_for_display: formatDateTime,
  convert_seconds_to_duration_for_display: formatDurationForDisplay,
};

const checkForSpiffFormats = (markdown: string) => {
  const replacer = (
    match: string,
    spiffFormat: string,
    originalValue: string
  ) => {
    if (spiffFormat in spiffFormatFunctions) {
      return spiffFormatFunctions[spiffFormat](undefined, originalValue);
    }
    console.warn(
      `attempted: ${match}, but ${spiffFormat} is not a valid conversion function`
    );

    return match;
  };
  return markdown.replaceAll(/SPIFF_FORMAT:::(\w+)\(([^)]+)\)/g, replacer);
};

const FormattingService = {
  checkForSpiffFormats,
};

export default FormattingService;

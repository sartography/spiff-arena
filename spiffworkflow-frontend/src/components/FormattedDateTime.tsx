import DateAndTimeService from '../services/DateAndTimeService';
import SpiffTooltip from './SpiffTooltip';

type OwnProps = {
  seconds: number | null | undefined;
  placeholder?: string;
};

/**
 * Renders a formatted date/time and, on hover, shows a tooltip that spells out
 * the timezone explicitly (e.g. "2024-05-12 21:37:00 (Europe/Berlin, GMT+2)")
 * so it is always obvious what timezone a datetime is in. See issue #1546.
 */
export default function FormattedDateTime({
  seconds,
  placeholder = '-',
}: OwnProps) {
  const formattedDateTime =
    seconds == null
      ? null
      : DateAndTimeService.convertSecondsToFormattedDateTime(seconds);
  if (!formattedDateTime) {
    return <span>{placeholder}</span>;
  }
  const formattedDateTimeWithTimezone =
    DateAndTimeService.convertSecondsToFormattedDateTimeWithTimezone(
      seconds as number,
    ) || formattedDateTime;
  return (
    <SpiffTooltip title={formattedDateTimeWithTimezone}>
      <span>{formattedDateTime}</span>
    </SpiffTooltip>
  );
}

// @ts-ignore
import { TimeAgo } from '../helpers/timeago';
import DateAndTimeService from '../services/DateAndTimeService';

type OwnProps = {
  timeInSeconds: number;
  onClick?: any;
  onKeyDown?: any;
};

export default function TableCellWithTimeAgoInWords({
  timeInSeconds,
  onClick = null,
  onKeyDown = null,
}: OwnProps) {
  return (
    <td
      title={
        DateAndTimeService.convertSecondsToFormattedDateTime(timeInSeconds) ||
        '-'
      }
      onClick={onClick}
      onKeyDown={onKeyDown}
    >
      {timeInSeconds ? TimeAgo.inWords(timeInSeconds) : '-'}
    </td>
  );
}

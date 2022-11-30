// @ts-ignore
import { TimeAgo } from '../helpers/timeago';
import { convertSecondsToFormattedDateTime } from '../helpers';

type OwnProps = {
  timeInSeconds: number;
};

export default function TableCellWithTimeAgoInWords({
  timeInSeconds,
}: OwnProps) {
  return (
    <td title={convertSecondsToFormattedDateTime(timeInSeconds) || '-'}>
      {timeInSeconds ? TimeAgo.inWords(timeInSeconds) : '-'}
    </td>
  );
}

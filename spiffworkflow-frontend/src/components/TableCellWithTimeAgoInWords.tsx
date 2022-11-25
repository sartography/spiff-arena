// @ts-ignore
import { TimeAgo } from '../helpers/timeago';
import { convertSecondsToFormattedDateTime } from '../helpers';

type OwnProps = {
  time_in_seconds: number;
};

export default function TableCellWithTimeAgoInWords({
  time_in_seconds,
}: OwnProps) {
  return (
    <td title={convertSecondsToFormattedDateTime(time_in_seconds) || '-'}>
      {time_in_seconds ? TimeAgo.inWords(time_in_seconds) : '-'}
    </td>
  );
}

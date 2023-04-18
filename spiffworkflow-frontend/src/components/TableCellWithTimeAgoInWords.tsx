// @ts-ignore
import { TimeAgo } from '../helpers/timeago';
import { convertSecondsToFormattedDateTime } from '../helpers';

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
    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-interactions
    <td
      title={convertSecondsToFormattedDateTime(timeInSeconds) || '-'}
      onClick={onClick}
      onKeyDown={onKeyDown}
    >
      {timeInSeconds ? TimeAgo.inWords(timeInSeconds) : '-'}
    </td>
  );
}

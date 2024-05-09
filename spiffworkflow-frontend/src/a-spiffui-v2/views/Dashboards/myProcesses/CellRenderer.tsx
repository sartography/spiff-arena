import { Chip, Stack, Typography } from '@mui/material';
import { formatSecondsForDisplay } from '../../../utils/Utils';

export default function CellRenderer({
  header,
  data,
}: {
  header: string;
  data: Record<string, any>;
}) {
  /** These values map to theme tokens, which enable the light/dark modes etc. */
  const chipBackground = (params: any) => {
    switch (params.value) {
      case 'Completed':
      case 'complete':
        return 'info';
      case 'Started':
        return 'success';
      case 'error':
        return 'error';
      case 'Wait a second':
      case 'user_input_required':
        return 'warning';
      default:
        return 'default';
    }
  };

  if (header === 'Last milestone' || header === 'Status') {
    return (
      <Chip
        label={data.value || '...no info...'}
        variant="filled"
        color={chipBackground(data)}
        sx={{
          width: '100%',
        }}
      />
    );
  }
  if (header === 'Start' || header === 'End') {
    return (
      <Stack
        direction="row"
        sx={{
          height: '100%',
          alignItems: 'center',
        }}
      >
        <Typography variant="body2">
          {formatSecondsForDisplay(data.value)}
        </Typography>
      </Stack>
    );
  }
  return (
    <Stack direction="row" sx={{ height: '100%', alignItems: 'center' }}>
      <Typography variant="body2">{data.value}</Typography>
    </Stack>
  );
}

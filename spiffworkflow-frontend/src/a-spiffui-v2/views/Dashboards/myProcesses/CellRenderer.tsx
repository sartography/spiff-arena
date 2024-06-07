import { Chip, Stack, Typography, useTheme } from '@mui/material';
import { formatSecondsForDisplay } from '../../../utils/Utils';

/** Used by the Processes datagrid in Dashboards to render things like chips on cells, etc. */
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
        return `info.${useTheme().palette.mode}`;
      case 'Started':
        return `success.${useTheme().palette.mode}`;
      case 'error':
        return `error.${useTheme().palette.mode}`;
      case 'Wait a second':
      case 'user_input_required':
        return `warning.${useTheme().palette.mode}`;
      default:
        return 'default';
    }
  };

  if (header === 'Last milestone' || header === 'Status') {
    return (
      <Stack
        sx={{
          justifyContent: 'center',
        }}
      >
        <Chip
          label={data.value || '...no info...'}
          variant="filled"
          sx={{
            width: '100%',
            borderRadius: 2,
            backgroundColor: chipBackground(data),
          }}
        />
      </Stack>
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

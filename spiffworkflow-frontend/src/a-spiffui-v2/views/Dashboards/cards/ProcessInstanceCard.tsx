import { Chip, Stack, Typography, useTheme } from '@mui/material';

/**
 * Appears when we need to display process instances in a responsive view.
 * Was quickly made for demo, likely will be redesigned, don't put a lot of effort here.
 */
export default function ProcessInstanceCard({
  pi,
}: {
  pi: Record<string, any>;
}) {
  const { mode } = useTheme().palette;
  /** These values map to theme tokens, which enable the light/dark modes etc. */
  const chipBackground = (status: string) => {
    switch (status) {
      case 'Completed':
      case 'complete':
        return `info.${mode}`;
      case 'Started':
        return `success.${mode}`;
      case 'error':
        return `error.${mode}`;
      case 'Wait a second':
      case 'user_input_required':
        return `warning.${mode}`;
      default:
        return 'default';
    }
  };

  return (
    <Stack
      gap={1}
      sx={{
        width: '100%',
        padding: 1,
        alignContent: 'center',
      }}
    >
      <Typography variant="button" sx={{ fontWeight: 600 }}>
        ({pi.row.tasks.length}) {pi.row.process_model_display_name}
      </Typography>

      <Stack direction="row" gap={2}>
        <Chip
          label={pi.row.status || '...no info...'}
          variant="filled"
          size="small"
          sx={{
            backgroundColor: chipBackground(pi.row.status),
            borderRadius: 1,
          }}
        />
        <Chip
          label={pi.row.last_milestone_bpmn_name || '...no info...'}
          variant="filled"
          size="small"
          sx={{
            borderRadius: 1,
            backgroundColor: chipBackground(pi.row.last_milestone_bpmn_name),
          }}
        />
      </Stack>
    </Stack>
  );
}

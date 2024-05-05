import { Divider, Grid, Stack, Typography, useTheme } from '@mui/material';
import { grey, purple } from '@mui/material/colors';

/**
 * Appears when we need to display process instances in a responsive view.
 * Was quickly made for demo.
 * TODO: Talk to designer about this.
 */
export default function ProcessInstanceCard({
  instance,
}: {
  instance: Record<string, any>;
}) {
  const isDark = useTheme().palette.mode === 'dark';
  const fontSize = 12;
  const fontWeight = 600;

  return (
    <Grid
      container
      gap={1}
      sx={{
        flex: 1,
        border: `2px solid ${purple[200]} `,
        padding: 2,
        borderRadius: 2,
        boxShadow: 3,
        color: isDark ? 'white' : 'text.primary',
      }}
    >
      <Grid item xs={12}>
        <Stack
          direction="row"
          alignItems="center"
          sx={{
            backgroundColor: isDark ? 'primary.main' : 'grey.200',
            borderRadius: 2,
            padding: 0.75,
            marginBottom: 1,
          }}
        >
          <Typography
            fontWeight={fontWeight}
            fontSize={fontSize + 1}
            sx={{ width: 200 }}
          >
            {instance.process_model_display_name}
          </Typography>
        </Stack>
        <Stack>
          <Typography fontWeight={fontWeight} fontSize={fontSize}>
            Started by:
          </Typography>
          <Typography fontSize={fontSize} paddingLeft={1}>
            {instance.process_initiator_username}
          </Typography>
        </Stack>
      </Grid>
      <Grid item>
        <Stack>
          <Typography fontWeight={fontWeight} fontSize={fontSize}>
            Last milestone:
          </Typography>
          <Typography fontSize={fontSize} paddingLeft={1}>
            {instance.last_milestone_bpmn_name}
          </Typography>
        </Stack>
        <Stack>
          <Typography fontWeight={fontWeight} fontSize={fontSize}>
            Status:
          </Typography>
          <Typography fontSize={fontSize} paddingLeft={1}>
            {instance.status}
          </Typography>
        </Stack>
      </Grid>
      <Grid item xs={6}>
        <Stack direction="row" gap={2} alignItems="center">
          <Typography fontWeight={fontWeight} fontSize={fontSize}>
            Id:
          </Typography>
          <Typography fontSize={fontSize}>{instance.id}</Typography>
        </Stack>
        <Stack direction="row" gap={2} alignItems="center">
          <Typography fontWeight={fontWeight} fontSize={fontSize}>
            Start:
          </Typography>
          <Typography fontSize={fontSize}>
            {instance.start_in_seconds}
          </Typography>
        </Stack>
        <Stack direction="row" gap={2} alignItems="center" paddingBottom={2}>
          <Typography fontWeight={fontWeight} fontSize={fontSize}>
            End:
          </Typography>
          <Typography fontSize={fontSize}>{instance.end_in_seconds}</Typography>
        </Stack>
      </Grid>
    </Grid>
  );
}

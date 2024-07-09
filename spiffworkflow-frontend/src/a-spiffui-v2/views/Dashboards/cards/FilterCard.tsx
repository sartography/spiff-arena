import { Paper, Stack, Typography, useTheme } from '@mui/material';
import { grey, purple } from '@mui/material/colors';

/**
 * Appears in the FilterCard area of the Dashboards view.
 * Doesn't do much else, probably will not be used elsewhere,
 * and will likely be redesigned, don't put in much effort here.
 */
export default function FilterCard({
  count,
  title,
}: {
  count: string;
  title: string;
}) {
  const isDark = useTheme().palette.mode === 'dark';
  return (
    <Paper
      sx={{
        border: `1px solid ${isDark ? grey[700] : grey[300]}`,
        borderRadius: 2,
        flexGrow: 1,
        ':hover': {
          backgroundColor: isDark ? 'primary.dark' : purple[50],
        },
      }}
    >
      <Stack direction="row" gap={2} padding={3} alignItems="center">
        <Typography variant="h4">{count}</Typography>
        <Typography>{title}</Typography>
      </Stack>
    </Paper>
  );
}

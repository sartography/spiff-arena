import { Stack, Typography } from '@mui/material';
import { grey, purple } from '@mui/material/colors';

/**
 * Appears in the FilterCard area of the Dashboards view.
 * Doesn't do much other than satisfy
 */
export default function FilterCard({
  count,
  title,
}: {
  count: string;
  title: string;
}) {
  return (
    <Stack
      direction="row"
      gap={2}
      padding={3}
      alignItems="center"
      sx={{
        backgroundColor: grey[200],
        height: 72,
        borderRadius: 2,
        flexGrow: 1,
        ':hover': { backgroundColor: purple[50] },
      }}
    >
      <Typography variant="h4">{count}</Typography>
      <Typography>{title}</Typography>
    </Stack>
  );
}

import { Paper, Stack, Typography } from '@mui/material';
import { Subject } from 'rxjs';

export default function ProcessGroupCard({
  group,
  stream,
}: {
  group: Record<string, any>;
  stream?: Subject<Record<string, any>>;
}) {
  const captionColor = 'text.secondary';

  return (
    <Paper
      elevation={0}
      sx={{
        borderRadius: 2,
        padding: 2,
        border: '1px solid',
        borderColor: 'borders.primary',
        minWidth: 320,
      }}
      onClick={() => stream && stream.next(group)}
    >
      <Stack>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          {group.display_name}
        </Typography>

        <Typography variant="caption" sx={{ color: captionColor }}>
          Groups: {group.process_groups.length}
        </Typography>
        <Typography variant="caption" sx={{ color: captionColor }}>
          Models: {group.process_models.length}
        </Typography>
      </Stack>
    </Paper>
  );
}

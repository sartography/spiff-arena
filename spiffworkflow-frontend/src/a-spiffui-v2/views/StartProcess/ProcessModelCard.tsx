import { Button, Paper, Stack, Typography } from '@mui/material';
import { Subject } from 'rxjs';

export default function ProcessModelCard({
  model,
  stream,
}: {
  model: Record<string, any>;
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
      onClick={() => stream && stream.next(model)}
    >
      <Stack>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          {model.display_name}
        </Typography>
        <Typography variant="body2" sx={{ fontWeight: 700 }}>
          {model.description || '--'}
        </Typography>

        <Typography variant="caption" sx={{ color: captionColor }}>
          ID: {model.id}
        </Typography>

        <Stack direction="row" sx={{ paddingTop: 2 }}>
          <Button variant="contained" color="primary" size="small">
            Start This Process
          </Button>
        </Stack>
      </Stack>
    </Paper>
  );
}

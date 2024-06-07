import { Paper, Stack, Typography, useTheme } from '@mui/material';
import { ReactNode } from 'react';
import { grey } from '@mui/material/colors';

/**
 * Appears in the TaskInfo fed to the InfoPanel.
 * Was quickly made for demo, likely will be redesigned, don't put a lot of effort here.
 */
export default function TaskListItem({
  task,
  icon,
  styleOverride,
}: {
  task: Record<string, any>;
  icon: ReactNode;
  styleOverride?: Record<string, any>;
}) {
  const isDark = useTheme().palette.mode === 'dark';
  return (
    <Paper
      key={task.id}
      elevation={3}
      sx={{
        ...{
          width: '100%',
          height: 75,
          borderRadius: 2,
          backgroundColor: isDark ? 'primary.main' : grey[200],
        },
        ...(styleOverride || {}),
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        sx={{
          width: '100%',
          height: '100%',
          gap: 2,
          padding: 1,
        }}
      >
        {icon}
        <Stack>
          <Typography sx={{ fontWeight: 600 }}>Status</Typography>
          <Typography>{task.task_status}</Typography>
        </Stack>
        <Stack>
          <Typography sx={{ fontWeight: 600 }}>Name</Typography>
          <Typography>{task.task_name}</Typography>
        </Stack>
        <Stack>
          <Typography sx={{ fontWeight: 600 }}>Title</Typography>
          <Typography>{task.task_title}</Typography>
        </Stack>
      </Stack>
    </Paper>
  );
}

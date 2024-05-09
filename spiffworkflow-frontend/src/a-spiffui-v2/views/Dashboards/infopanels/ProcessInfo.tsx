import {
  Box,
  Divider,
  Paper,
  Stack,
  Typography,
  useTheme,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { grey } from '@mui/material/colors';
import useTaskCollection from '../../../hooks/useTaskCollection';
import { formatSecondsForDisplay } from '../../../utils/Utils';
import GreenCircleCheck from '../../../assets/icons/green-circle-check.svg';
import WarningEye from '../../../assets/icons/warning-eye.svg';
import useCompletedTasks from '../../../hooks/useCompletedTasks';

export default function ProcessInfo({ data }: { data: Record<string, any> }) {
  const { taskCollection } = useTaskCollection({ processInfo: data });
  const { completedTasks } = useCompletedTasks({ processInfo: data });
  const [filteredTasks, setFilteredTasks] = useState<Record<string, any>[]>([]);
  const isDark = useTheme().palette.mode === 'dark';

  useEffect(() => {
    if ('results' in taskCollection) {
      setFilteredTasks(
        taskCollection.results.filter(
          (task: Record<string, any>) => task.process_instance_id === data.id
        )
      );
    }
  }, [taskCollection]);

  return (
    <Stack
      sx={{
        width: '100%',
        height: '100%',
        padding: 2,
        gap: 2,
      }}
    >
      <Stack direction="row" gap={4}>
        <Stack gap={2}>
          <Box>
            <Typography variant="h6">Last Milestone</Typography>
            <Typography variant="body1" sx={{ paddingLeft: 2 }}>
              {data.last_milestone_bpmn_name}
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6">Started</Typography>
            <Typography variant="body1" sx={{ paddingLeft: 2 }}>
              {formatSecondsForDisplay(data.start_in_seconds)}
            </Typography>
          </Box>
        </Stack>
        <Stack gap={2}>
          <Box>
            <Typography variant="h6">Status</Typography>
            <Typography variant="body1" sx={{ paddingLeft: 2 }}>
              {data.status}
            </Typography>
          </Box>
          <Box>
            <Typography variant="h6">Initiated By</Typography>
            <Typography variant="body1" sx={{ paddingLeft: 2 }}>
              {data.process_initiator_username}
            </Typography>
          </Box>
        </Stack>
      </Stack>
      <Divider variant="fullWidth" sx={{ backgroundColor: 'grey' }} />
      <Typography variant="h6">Tasks</Typography>
      <Stack
        sx={{
          gap: 2,
          overflow: 'auto',
          height: `calc(100% - 260px)`,
        }}
      >
        {!completedTasks.length && (
          <Typography color={isDark ? 'success.light' : 'success.dark'}>
            No Completed Tasks
          </Typography>
        )}
        {completedTasks.map((task: Record<string, any>) => (
          <Paper
            key={task.id}
            elevation={3}
            sx={{
              width: '100%',
              height: 75,
              borderRadius: 4,
              backgroundColor: isDark ? 'primary.main' : grey[200],
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
              <GreenCircleCheck />
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
        ))}
        {!filteredTasks.length && (
          <Typography color="warning.dark">No Open Tasks</Typography>
        )}
        {filteredTasks.map((task: Record<string, any>) => (
          <Paper
            key={task.id}
            elevation={3}
            sx={{
              width: '100%',
              height: 75,
              borderRadius: 4,
              backgroundColor: isDark ? 'primary.main' : grey[200],
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
              <WarningEye />
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
        ))}
      </Stack>
    </Stack>
  );
}

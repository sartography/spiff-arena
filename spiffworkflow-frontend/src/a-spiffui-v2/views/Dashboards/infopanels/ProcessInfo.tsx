import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Divider,
  Stack,
  Typography,
} from '@mui/material';
import { useEffect, useState } from 'react';
import { GridExpandMoreIcon } from '@mui/x-data-grid';
import useTaskCollection from '../../../hooks/useTaskCollection';
import { formatSecondsForDisplay } from '../../../utils/Utils';
import useCompletedTasks from '../../../hooks/useCompletedTasks';
import useSpiffTheme from '../../../hooks/useSpiffTheme';
import TaskListItem from './TaskListItem';
import GreenCircleCheck from '../../../assets/icons/green-circle-check.svg';
import WarningEye from '../../../assets/icons/warning-eye.svg';

export default function ProcessInfo({ data }: { data: Record<string, any> }) {
  const { taskCollection } = useTaskCollection({ processInfo: data });
  const { completedTasks } = useCompletedTasks({ processInfo: data });
  const [filteredTasks, setFilteredTasks] = useState<Record<string, any>[]>([]);
  const { isDark } = useSpiffTheme();

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
      <Stack
        sx={{
          gap: 2,
          overflow: 'auto',
          height: `calc(100% - 260px)`,
        }}
      >
        <Accordion
          sx={{
            borderRadius: 2,
            border: '2px solid',
            borderColor: isDark ? 'success.dark' : 'success.light',
          }}
        >
          <AccordionSummary
            expandIcon={<GridExpandMoreIcon />}
            aria-controls="completed-tasks-content"
            id="completed-tasks"
          >
            <Typography variant="button">
              {completedTasks.length
                ? `(${completedTasks.length}) Completed Tasks`
                : 'No Completed Tasks'}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Stack gap={2}>
              {completedTasks.map((task: Record<string, any>) => (
                <TaskListItem task={task} icon={<GreenCircleCheck />} />
              ))}
            </Stack>
          </AccordionDetails>
        </Accordion>
        <Accordion
          defaultExpanded
          sx={{
            borderRadius: 2,
            border: '2px solid',
            borderColor: `warning.${isDark ? 'dark' : 'light'}`,
          }}
        >
          <AccordionSummary
            expandIcon={<GridExpandMoreIcon />}
            aria-controls="panel1-content"
            id="panel1-header"
          >
            <Typography variant="button">
              {filteredTasks.length
                ? `(${filteredTasks.length}) Open Tasks`
                : 'No Open Tasks'}
            </Typography>
          </AccordionSummary>
          <AccordionDetails>
            <Stack gap={2}>
              {filteredTasks.map((task: Record<string, any>) => (
                <TaskListItem task={task} icon={<WarningEye />} />
              ))}
            </Stack>
          </AccordionDetails>
        </Accordion>
      </Stack>
    </Stack>
  );
}

import { Box } from '@mui/material';
import { ReactNode } from 'react';

const path = `/task-data/modified_process_model_identifier/process_instance_id/task_guid`;

/**
 * Appears when we need to display task details in an InfoPanel.
 * Was quickly made for demo, likely will be redesigned, don't put a lot of effort here.
 */
export default function TaskDetail({
  task,
  icon,
  styleOverride,
}: {
  task: Record<string, any>;
  icon: ReactNode;
  styleOverride?: Record<string, any>;
}) {
  return (
    <Box sx={{ ...styleOverride }}>
      <Box>{path}</Box>
      <Box>{icon}</Box>
      <Box>{task.task_guid}</Box>;
    </Box>
  );
}

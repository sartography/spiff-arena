import { Box } from '@mui/material';

/**
 * Appears when we need to display the Process Info in the InfoPanel.
 * Was quickly made for demo, likely will be redesigned, don't put a lot of effort here.
 */
export default function TaskInfo({ data }: { data: Record<string, any> }) {
  return (
    <Box
      sx={{
        position: 'relative',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
        zIndex: 0,
      }}
    >
      <iframe
        width="100%"
        height="100%"
        title="The Task"
        src={`${window.location.protocol || 'http'}//${
          window.location.host || 'localhost:7001'
        }/tasks/${data.process_instance_id}/${data.task_guid}`}
      />
    </Box>
  );
}

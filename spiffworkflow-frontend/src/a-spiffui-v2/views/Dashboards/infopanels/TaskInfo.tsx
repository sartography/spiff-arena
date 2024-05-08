import { Box } from '@mui/material';
import { useEffect } from 'react';

export default function TaskInfo({ data }: { data: Record<string, any> }) {
  useEffect(() => {
    console.log(data);
  }, [data]);

  return (
    <Box
      sx={{
        position: 'relative',
        top: -50,
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
        src={`http://localhost:7001/tasks/${data.process_instance_id}/${data.task_guid}`}
      />
    </Box>
  );
}

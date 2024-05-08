import { Box, Typography } from '@mui/material';
import { useEffect } from 'react';

export default function ProcessInfo({ data }: { data: Record<string, any> }) {
  useEffect(() => {
    console.log(data);
  }, [data]);

  return (
    <Box
      sx={{
        width: '100%',
        height: '100%',
      }}
    >
      <Typography variant="h1">Hello everybody</Typography>
      <Typography variant="h1">Hello everybody</Typography>
    </Box>
  );
}

import { Box, Paper } from '@mui/material';

export default function InfoWindow({ data }: { data: Record<string, any> }) {
  return (
    <Box sx={{ padding: 2, width: '100%', height: '100%' }}>
      <Paper
        variant="elevation"
        color="spiff.greyBorder"
        sx={{
          width: '100%',
          height: '100%',
          border: '1px solid',
          borderRadius: 4,
        }}
      >
        <h1>Hello</h1>
      </Paper>
    </Box>
  );
}

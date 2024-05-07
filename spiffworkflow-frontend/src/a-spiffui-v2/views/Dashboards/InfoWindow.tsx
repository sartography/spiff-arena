import {
  Box,
  IconButton,
  Paper,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material';
import { Close } from '@mui/icons-material';
import { useEffect } from 'react';

export default function InfoWindow({ data }: { data: Record<string, any> }) {
  useEffect(() => {
    console.log(data);
  }, [data]);
  return (
    <Box sx={{ width: '100%', height: '100%' }}>
      <Paper
        elevation={10}
        sx={{
          width: '100%',
          height: '100%',
          border: '4px solid',
          borderColor: 'primary.light',
          borderRadius: 2,
          padding: 1,
        }}
      >
        <Stack>
          {/* <Toolbar variant="regular">
            <IconButton edge="start" color="inherit" aria-label="close">
              <Close />
            </IconButton>
            <Typography variant="h1">
              {data.row.process_model_display_name}
            </Typography>
          </Toolbar>

          <Typography>{data.row.process_initiator_username}</Typography>
          <Typography>{data.row.last_milestone_bpmn_name}</Typography>
          <Typography>{data.row.last_milestone_bpmn_name}</Typography> */}
        </Stack>
      </Paper>
    </Box>
  );
}

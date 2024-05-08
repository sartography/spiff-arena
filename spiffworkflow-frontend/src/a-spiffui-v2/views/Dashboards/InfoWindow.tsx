import {
  Box,
  IconButton,
  Paper,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import { useEffect } from 'react';

export default function InfoWindow({
  data,
  callback,
}: {
  data: Record<string, any>;
  callback: () => void;
}) {
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
        <Stack sx={{ height: '100%', position: 'relative' }}>
          <Box
            sx={{
              position: 'absolute',
              top: 0,
              left: 0,
              zIndex: 9999,
              backgroundColor: 'white',
              width: '100%',
            }}
          >
            <Toolbar variant="regular">
              <IconButton
                edge="start"
                color="inherit"
                aria-label="close"
                onClick={() => callback()}
              >
                <CloseOutlinedIcon />
              </IconButton>
              <Typography variant="h6">
                {data.process_model_display_name}
              </Typography>
            </Toolbar>
          </Box>
          <Box
            sx={{
              width: '100%',
              height: '100%',
              position: 'absolute',
              top: 0,
              left: 0,
              zIndex: 0,
            }}
          >
            <iframe
              width="100%"
              height="100%"
              title="The Task"
              src="http://localhost:7001/tasks/16/1deef7a0-59a5-4607-a840-30e7edb6f872"
            />
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}

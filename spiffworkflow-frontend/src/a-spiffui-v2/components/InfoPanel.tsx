import {
  Box,
  IconButton,
  Paper,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material';
import CloseOutlinedIcon from '@mui/icons-material/CloseOutlined';
import { ReactNode } from 'react';

export default function InfoPanel({
  title,
  callback,
  children,
}: {
  title: string;
  callback: () => void;
  children: ReactNode;
}) {
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
              <Typography variant="h6">{title}</Typography>
            </Toolbar>
          </Box>
          <Box sx={{ position: 'relative', top: 60, height: '100%' }}>
            {children}
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}

import {
  Box,
  IconButton,
  Paper,
  Stack,
  Toolbar,
  Typography,
  useTheme,
} from '@mui/material';
import CancelOutlinedIcon from '@mui/icons-material/CancelOutlined';
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
  const isDark = useTheme().palette.mode === 'dark';
  return (
    <Box sx={{ width: '100%', height: '100%' }}>
      <Paper
        elevation={10}
        sx={{
          width: '100%',
          height: '100%',
          border: '4px solid',
          borderColor: 'primary.main',
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
              width: '100%',
            }}
          >
            <Toolbar
              variant="regular"
              sx={{
                backgroundColor: isDark ? 'primary.dark' : 'primary.light',
                borderRadius: 3,
              }}
            >
              <IconButton
                edge="start"
                color="inherit"
                aria-label="close"
                onClick={() => callback()}
                sx={{
                  marginRight: 2,
                  backgroundColor: isDark ? 'primary.dark' : 'primary.light',
                }}
              >
                <CancelOutlinedIcon />
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

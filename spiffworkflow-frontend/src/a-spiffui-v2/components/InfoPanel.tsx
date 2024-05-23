import { Box, Paper, Stack } from '@mui/material';
import { ReactNode } from 'react';
import CollapseButton from '../views/app/sidemenu/CollapseButton';

export default function InfoPanel({
  title,
  callback,
  children,
}: {
  title: string;
  callback: () => void;
  children: ReactNode;
}) {
  const handleClose = () => {
    callback();
  };

  return (
    <Box
      sx={{
        width: 'calc(100% - 20px)',
        height: '100%',
        resize: 'both',
        position: 'relative',
      }}
    >
      <Box
        sx={{
          position: 'absolute',
          top: '50%',
          left: -12,
          backgroundColor: 'background.paper',
          zIndex: 2000, // MUI top level
        }}
      >
        <CollapseButton callback={handleClose} />
      </Box>
      <Paper
        elevation={4}
        sx={{
          width: '100%',
          height: '100%',
          border: '1px solid',
          borderColor: 'divider',
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
              zIndex: 1500, // MUI top level
              width: '100%',
              height: '100%',
            }}
          >
            {children}
          </Box>
        </Stack>
      </Paper>
    </Box>
  );
}

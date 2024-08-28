import React from 'react';
import { Box, Typography, Link as MuiLink } from '@mui/material';
import { Link } from 'react-router-dom';

function ComingSoon() {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100vh',
      }}
    >
      <Typography variant="h1" gutterBottom>
        Coming Soon
      </Typography>
      <Typography variant="h6">This feature will be available soon.</Typography>
      <MuiLink component={Link} to="/newui" variant="h6" sx={{ mt: 2 }}>
        Go back home
      </MuiLink>
    </Box>
  );
}

export default ComingSoon;

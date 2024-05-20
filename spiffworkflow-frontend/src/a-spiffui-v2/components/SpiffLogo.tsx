import { Stack, Typography } from '@mui/material';
import SpiffIcon from '../assets/icons/spiff-icon-cyan.svg';

/**
 * The Spiff "S" logo and approved text
 */
export default function SpiffLogo() {
  return (
    <Stack sx={{ alignItems: 'center' }}>
      <Stack direction="row" sx={{ alignItems: 'center', gap: 2 }}>
        <SpiffIcon />
        <Typography
          sx={{
            color: 'primary.main',
            fontSize: 22,
            display: { xs: 'none', md: 'block' },
          }}
        >
          Spiffworkflow
        </Typography>
      </Stack>
    </Stack>
  );
}

import { Stack, Typography } from '@mui/material';
import { purple } from '@mui/material/colors';
import SpiffIcon from '../assets/icons/spiff-icon.svg';

export default function SpiffLogo() {
  return (
    <Stack alignItems="center" height={80}>
      <Stack direction="row" alignItems="center" padding={2}>
        <SpiffIcon />
        <Typography color={purple[700]} sx={{ fontSize: 20 }}>
          Spiffworkflow
        </Typography>
      </Stack>
    </Stack>
  );
}

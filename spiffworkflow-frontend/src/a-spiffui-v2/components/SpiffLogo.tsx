import { Stack, Typography } from '@mui/material';
import SpiffIcon from '../assets/icons/spiff-icon.svg';

export default function SpiffLogo() {
  return (
    <Stack direction="row">
      <SpiffIcon />
      <Typography>Spiffworkflow</Typography>
    </Stack>
  );
}

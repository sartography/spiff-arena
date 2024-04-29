import { Stack, Typography } from '@mui/material';
import SpiffLogo from '../../assets/SpiffLogo.svg';

export default function SideMenu() {
  return (
    <Stack width="240px">
      <Typography>Joe Momma</Typography>
      <SpiffLogo />
      <Typography>Jobeki</Typography>
    </Stack>
  );
}

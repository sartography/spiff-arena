import { Divider, Stack } from '@mui/material';
import SideMenu from '../a-spiffui-v2/components/sidemenu/SideMenu';
import { grey } from '@mui/material/colors';

export default function SpiffUIV2() {
  return (
    <Stack
      direction="row"
      spacing={8}
      divider={
        <Divider
          orientation="vertical"
          sx={{ height: '100%', backgroundColor: 'grey' }}
        />
      }
      sx={{
        position: 'absolute',
        top: 0,
        left: 0,
        width: '100%',
        height: '100%',
      }}
    >
      <Stack>
        <SideMenu />
      </Stack>
      <Stack>Content</Stack>
    </Stack>
  );
}

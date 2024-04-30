import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Divider, Stack } from '@mui/material';
import SideMenu from '../a-spiffui-v2/components/sidemenu/SideMenu';
import Dashboards from '../a-spiffui-v2/views/Dashboards/Dashboards';
import { globalTheme } from '../a-spiffui-v2/assets/theme/SpiffTheme';

export default function SpiffUIV2() {
  const muiTheme = createTheme(globalTheme);

  return (
    <ThemeProvider theme={muiTheme}>
      <Stack
        direction="row"
        gap={2}
        padding={2}
        divider={
          <Divider
            orientation="vertical"
            sx={{ height: '100%', backgroundColor: 'grey' }}
          />
        }
        sx={{
          // Hack to position the internal view over the "old" base components
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
        <Stack width="100%" height="100%" padding={2}>
          <Dashboards />
        </Stack>
      </Stack>
    </ThemeProvider>
  );
}

import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Divider, Stack } from '@mui/material';
import SideMenu from '../a-spiffui-v2/components/sidemenu/SideMenu';
import Dashboards from '../a-spiffui-v2/views/Dashboards/Dashboards';

export default function SpiffUIV2() {
  const muiTheme = createTheme({
    palette: {
      primary: { main: '#6750A4' },
      secondary: { main: '#625B71' },
    },
    typography: {
      fontFamily: `"Poppins", "Roboto", "Arial", "Helvetica", sans-serif`,
      fontSize: 14,
      fontWeightLight: 300,
      fontWeightRegular: 400,
      fontWeightMedium: 500,
      button: {
        textTransform: 'none',
      },
    },
    components: {
      // Name of the component
      MuiButton: {
        styleOverrides: {
          root: {
            fontSize: '1rem',
            borderRadius: 100,
          },
        },
      },
    },
  });

  return (
    <ThemeProvider theme={muiTheme}>
      <Stack
        direction="row"
        gap={2}
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
        <Stack>
          <Dashboards />
        </Stack>
      </Stack>
    </ThemeProvider>
  );
}

import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, Container, Divider, Grid } from '@mui/material';
import { grey } from '@mui/material/colors';
import SideMenu from '../a-spiffui-v2/components/sidemenu/SideMenu';
import Dashboards from '../a-spiffui-v2/views/Dashboards/Dashboards';
import { globalTheme } from '../a-spiffui-v2/assets/theme/SpiffTheme';

export default function SpiffUIV2() {
  const muiTheme = createTheme(globalTheme);

  return (
    <ThemeProvider theme={muiTheme}>
      <Container
        maxWidth={false}
        sx={{
          // Hack to position the internal view over the "old" base components
          position: 'absolute',
          top: 0,
          left: 0,
          alignItems: 'center',
          width: '100%',
          height: '100%',
        }}
      >
        <Grid container sx={{ height: '100%' }}>
          <Grid item>
            <Box sx={{ display: { xs: 'none', md: 'block' }, height: '100%' }}>
              <SideMenu />
            </Box>
          </Grid>
          <Grid
            item
            padding={2}
            sx={{ display: { xs: 'none', md: 'block' }, height: '100%' }}
          >
            <Divider
              orientation="vertical"
              variant="middle"
              sx={{
                width: '1px',
                height: '100%',
                backgroundColor: grey[600],
              }}
            />
          </Grid>
          <Grid item xs={4} sm={12} md={8} lg={9} xl={10} padding={2}>
            <Dashboards />
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

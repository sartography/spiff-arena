import { ThemeProvider, createTheme } from '@mui/material/styles';
import {
  Box,
  Container,
  CssBaseline,
  Divider,
  Grid,
  Paper,
  Slide,
} from '@mui/material';
import { grey } from '@mui/material/colors';
import { useEffect, useState } from 'react';
import SideMenu from '../a-spiffui-v2/views/app/sidemenu/SideMenu';
import Dashboards from '../a-spiffui-v2/views/Dashboards/Dashboards';
import { createSpiffTheme } from '../a-spiffui-v2/assets/theme/SpiffTheme';
import { MenuItemData } from '../a-spiffui-v2/views/app/sidemenu/MenuItem';
import CollapseButton from '../a-spiffui-v2/views/app/sidemenu/CollapseButton';

/**
 * This is the main entry point for the new SpiffUI V2.
 * It's a full screen app that will be rendered on top of the old SpiffUI.
 * To access, use the root domain (e.g. localhost:7001) and add"/newui"
 */
export default function SpiffUIV2() {
  const [globalTheme, setGlobalTheme] = useState(
    createTheme(createSpiffTheme('light'))
  );
  const [sideMenuCollapsed, setSideMenuCollapsed] = useState(false);
  useEffect(() => {
    /**
     * The housing app has an element with a white background
     * and a very high z-index. This is a hack to remove it.
     */
    const element = document.querySelector('.cds--white');
    if (element) {
      element.classList.remove('cds--white');
    }
  }, []);

  const handleMenuCallback = (data: MenuItemData) => {
    if (data.text === 'Dark Mode') {
      if (globalTheme.palette.mode === 'light') {
        setGlobalTheme(createTheme(createSpiffTheme('dark')));
      } else {
        setGlobalTheme(createTheme(createSpiffTheme('light')));
      }
    }
  };

  const handleCollapseToggle = (data: boolean) => {
    setSideMenuCollapsed(data);
  };

  return (
    <ThemeProvider theme={globalTheme}>
      <CssBaseline />
      <Container
        maxWidth={false}
        sx={{
          // Hack to position the internal view over the "old" base components
          position: 'absolute',
          top: 0,
          left: 0,
          alignItems: 'center',
          height: '100vh',
          zIndex: 1000,
          padding: '0px !important',
        }}
      >
        <Grid container sx={{ height: '100%' }}>
          <Grid item>
            <Slide direction="right" in mountOnEnter unmountOnExit>
              <Box
                sx={{
                  height: '100%',
                  width: '100%',
                  position: 'relative',
                }}
              >
                <Paper
                  elevation={3}
                  sx={{ padding: 2, margin: 0, width: '100%', height: '100%' }}
                >
                  <SideMenu
                    callback={handleMenuCallback}
                    collapsed={sideMenuCollapsed}
                  />
                </Paper>
                <Box
                  sx={{
                    position: 'absolute',
                    top: '28%',
                    right: -25,
                    zIndex: 1500,
                    display: { xs: 'none', lg: 'block' },
                  }}
                >
                  <CollapseButton callback={handleCollapseToggle} />
                </Box>
              </Box>
            </Slide>
          </Grid>
          <Grid
            item
            xs={10}
            sm={10}
            md={sideMenuCollapsed ? 11 : 8}
            lg={sideMenuCollapsed ? 11 : 9}
            padding={6}
          >
            <Dashboards />
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, Container, CssBaseline, Grid, Slide } from '@mui/material';
import { useEffect, useState } from 'react';
import Dashboards from '../a-spiffui-v2/views/Dashboards/Dashboards';
import { createSpiffTheme } from '../a-spiffui-v2/assets/theme/SpiffTheme';
import { MenuItemData } from '../a-spiffui-v2/views/app/sidemenu/MenuItem';
import TopMenu from '../a-spiffui-v2/views/Dashboards/TopMenu';

/**
 * This is the main entry point for the new SpiffUI V2.
 * It's a full screen app that will be rendered on top of the old SpiffUI.
 * To access, use the root domain (e.g. localhost:7001) and add"/newui"
 */
export default function SpiffUIV2() {
  const [globalTheme, setGlobalTheme] = useState(
    createTheme(createSpiffTheme('light'))
  );
  const isDark = globalTheme.palette.mode === 'dark';
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
          overflow: 'hidden',
        }}
      >
        <Grid
          container
          sx={{
            height: '100%',
            backgroundColor: isDark
              ? 'background.paper'
              : 'background.mediumlight',
          }}
        >
          <Grid item sx={{ width: '100%' }}>
            <Slide direction="down" in mountOnEnter unmountOnExit>
              <Box
                sx={{
                  height: '100%',
                  width: '100%',
                  position: 'relative',
                }}
              >
                <Box
                  sx={{
                    width: '100%',
                  }}
                >
                  <TopMenu callback={handleMenuCallback} />
                </Box>
              </Box>
            </Slide>
          </Grid>
          <Grid item xs={12} sx={{ padding: '3%' }}>
            <Dashboards />
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

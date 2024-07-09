import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Box, Container, CssBaseline, Grid, Slide } from '@mui/material';
import { useEffect, useState } from 'react';
import { Route, Routes, useLocation, useNavigate } from 'react-router';
import Dashboards from '../a-spiffui-v2/views/Dashboards/Dashboards';
import { createSpiffTheme } from '../a-spiffui-v2/assets/theme/SpiffTheme';
import { MenuItemData } from '../a-spiffui-v2/views/app/topmenu/MenuItem';
import TopMenu from '../a-spiffui-v2/views/app/topmenu/TopMenu';
import StartProcess from '../a-spiffui-v2/views/StartProcess/StartProcess';

/**
 * This is the main entry point for the new SpiffUI V2.
 * It's a full screen app that will be rendered on top of the old SpiffUI.
 * To access, use the root domain (e.g. localhost:7001) and add"/newui"
 */
export default function SpiffUIV2() {
  const [globalTheme, setGlobalTheme] = useState(
    createTheme(createSpiffTheme('light')),
  );
  const navigate = useNavigate();
  const isDark = globalTheme.palette.mode === 'dark';
  const location = useLocation();

  const [displayLocation, setDisplayLocation] = useState(location);
  const [transitionStage, setTransistionStage] = useState('fadeIn');

  const fadeIn = 'fadeIn';
  const fadeOutImmediate = 'fadeOutImmediate';

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

  /** Respond to transition events, this softens screen changes (UX) */
  useEffect(() => {
    if (location !== displayLocation) {
      setTransistionStage(fadeOutImmediate);
    }
  }, [location, displayLocation]);

  /** One of the TopMenu MenuItems was clicked */
  const handleMenuCallback = (data: MenuItemData) => {
    // Some TopMenu buttons are for navigation, some aren't
    if (data?.text === 'Dark Mode') {
      setGlobalTheme(
        createTheme(
          createSpiffTheme(
            globalTheme.palette.mode === 'light' ? 'dark' : 'light',
          ),
        ),
      );
    } else if (data?.path) {
      navigate(data.path);
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
          <Grid item xs={12} sx={{ height: '100%' }}>
            <Box
              className={`${transitionStage}`}
              sx={{
                width: '100%',
                height: '100%',
              }}
              onAnimationEnd={() => {
                if (transitionStage === fadeOutImmediate) {
                  setTransistionStage(fadeIn);
                  setDisplayLocation(location);
                }
              }}
            >
              <Routes>
                <Route path="/" element={<Dashboards />} />
                <Route path="/dashboard" element={<Dashboards />} />
                <Route path="/startprocess" element={<StartProcess />} />
              </Routes>
            </Box>
          </Grid>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

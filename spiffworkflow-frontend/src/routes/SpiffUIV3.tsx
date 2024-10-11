import React, { useState, useEffect, ReactElement } from 'react';
import {
  PaletteMode,
  Box,
  Container,
  CssBaseline,
  IconButton,
  Grid,
  ThemeProvider,
  useMediaQuery,
  createTheme,
} from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import { Route, Routes, useLocation } from 'react-router';
import { createSpiffTheme } from '../a-spiffui-v3/assets/theme/SpiffTheme';
import Homepage from '../a-spiffui-v3/views/Homepage';
import '../a-spiffui-v3/assets/styles/transitions.css';
import StartProcess from '../a-spiffui-v3/views/StartProcess/StartProcess';
import StartProcessInstance from '../a-spiffui-v3/views/StartProcess/StartProcessInstance';
import SideNav from '../a-spiffui-v3/components/SideNav';
import LoginHandler from '../components/LoginHandler';
import Login from './Login';
import InstancesStartedByMe from '../a-spiffui-v3/views/InstancesStartedByMe';
import TaskShow from '../a-spiffui-v3/views/TaskShow/TaskShow';
import ProcessInterstitialPage from '../a-spiffui-v3/views/TaskShow/ProcessInterstitialPage';
import ProcessInstanceProgressPage from '../a-spiffui-v3/views/TaskShow/ProcessInstanceProgressPage';
import ErrorDisplay from '../components/ErrorDisplay';
import About from '../a-spiffui-v3/views/About';
import useAPIError from '../hooks/UseApiError';
import ComingSoon from '../components/ComingSoon';

const fadeIn = 'fadeIn';
const fadeOutImmediate = 'fadeOutImmediate';

export default function SpiffUIV3() {
  const storedTheme: PaletteMode = (localStorage.getItem('theme') ||
    'light') as PaletteMode;
  const [globalTheme, setGlobalTheme] = useState(
    createTheme(createSpiffTheme(storedTheme)),
  );
  const isDark = globalTheme.palette.mode === 'dark';
  const location = useLocation();

  const [displayLocation, setDisplayLocation] = useState(location);
  const [transitionStage, setTransitionStage] = useState('fadeIn');
  const [isLongFadeIn, setIsLongFadeIn] = useState(false);
  const [additionalNavElement, setAdditionalNavElement] =
    useState<ReactElement | null>(null);

  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);

  const isMobile = useMediaQuery((theme: any) => theme.breakpoints.down('sm'));
  const [isSideNavVisible, setIsSideNavVisible] = useState<boolean>(!isMobile);
  const [viewMode, setViewMode] = useState<'table' | 'tile'>(
    isMobile ? 'tile' : 'table',
  );
  const { removeError } = useAPIError();

  const toggleNavCollapse = () => {
    if (isMobile) {
      setIsSideNavVisible(!isSideNavVisible);
    } else {
      setIsNavCollapsed(!isNavCollapsed);
    }
    if (isMobile) {
      setIsSideNavVisible(!isSideNavVisible);
    } else {
      setIsNavCollapsed(!isNavCollapsed);
    }
  };

  const toggleDarkMode = () => {
    const desiredTheme: PaletteMode = isDark ? 'light' : 'dark';
    setGlobalTheme(createTheme(createSpiffTheme(desiredTheme)));
    localStorage.setItem('theme', desiredTheme);
  };

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
  // never carry an error message across to a different path
  useEffect(() => {
    removeError();
    // if we include the removeError function to the dependency array of this useEffect, it causes
    // an infinite loop where the page with the error adds the error,
    // then this runs and it removes the error, etc. it is ok not to include it here, i think, because it never changes.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.pathname]);

  /** Respond to transition events, this softens screen changes (UX) */
  useEffect(() => {
    if (location !== displayLocation) {
      const isComingFromInterstitialOrProgress =
        /\/interstitial$|\/progress$/.test(displayLocation.pathname);
      setIsLongFadeIn(
        isComingFromInterstitialOrProgress && location.pathname === '/newui',
      );
      setTransitionStage(fadeOutImmediate);
    }
    if (transitionStage === fadeOutImmediate) {
      setDisplayLocation(location);
      setTransitionStage(fadeIn);
    }
  }, [location, displayLocation, transitionStage]);

  useEffect(() => {
    if (isMobile) {
      setIsSideNavVisible(false);
    } else {
      setIsSideNavVisible(true);
      setIsNavCollapsed(false);
    }
  }, [isMobile]);

  return (
    <ThemeProvider theme={globalTheme}>
      <LoginHandler />
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
        <Grid
          container
          sx={{
            height: '100%',
          }}
        >
          <Box
            sx={{
              display: 'flex',
              width: '100%',
              height: '100vh',
              overflow: 'hidden',
            }}
          >
            {isSideNavVisible && (
              <SideNav
                isCollapsed={isNavCollapsed}
                onToggleCollapse={toggleNavCollapse}
                onToggleDarkMode={toggleDarkMode}
                isDark={isDark}
                additionalNavElement={additionalNavElement}
                setAdditionalNavElement={setAdditionalNavElement}
              />
            )}
            {isMobile && !isSideNavVisible && (
              <IconButton
                onClick={() => {
                  setIsSideNavVisible(true);
                  setIsNavCollapsed(false);
                }}
                sx={{ position: 'absolute', top: 16, right: 16, zIndex: 1300 }}
              >
                <MenuIcon />
              </IconButton>
            )}
            <Box
              className={`${transitionStage}`}
              sx={{
                bgcolor: 'background.default',
                width: '100%',
                height: '100%',
                display: 'flex',
                flexDirection: 'column',
                flexGrow: 1,
                overflow: 'auto',
              }}
              onAnimationEnd={(e) => {
                if (e.animationName === fadeOutImmediate) {
                  setDisplayLocation(location);
                  setTransitionStage(fadeIn);
                }
              }}
            >
              <ErrorDisplay />
              <Routes>
                <Route path="/about" element={<About />} />
                <Route
                  path="/"
                  element={
                    <Homepage
                      viewMode={viewMode}
                      setViewMode={setViewMode}
                      isMobile={isMobile}
                      isLongFadeIn={isLongFadeIn}
                    />
                  }
                />
                <Route
                  path="/startprocess"
                  element={
                    <StartProcess
                      setNavElementCallback={setAdditionalNavElement}
                    />
                  }
                />
                <Route
                  path="/:modifiedProcessModelId/start"
                  element={<StartProcessInstance />}
                />
                <Route path="login" element={<Login />} />
                <Route path="/create-custom-tab" element={<ComingSoon />} />
                <Route
                  path="/tasks/:process_instance_id/:task_guid"
                  element={<TaskShow />}
                />
                <Route
                  path="/started-by-me"
                  element={
                    <InstancesStartedByMe
                      viewMode={viewMode}
                      setViewMode={setViewMode}
                      isMobile={isMobile}
                    />
                  }
                />
                <Route
                  path="process-instances/for-me/:process_model_id/:process_instance_id/interstitial"
                  element={<ProcessInterstitialPage variant="for-me" />}
                />
                {/* <Route */}
                {/*   path="process-instances/:process_model_id/:process_instance_id/interstitial" */}
                {/*   element={<ProcessInterstitialPage variant="all" />} */}
                {/* /> */}
                <Route
                  path="process-instances/for-me/:process_model_id/:process_instance_id/progress"
                  element={<ProcessInstanceProgressPage variant="for-me" />}
                />
                {/* <Route */}
                {/*   path="process-instances/:process_model_id/:process_instance_id/progress" */}
                {/*   element={<ProcessInstanceProgressPage variant="all" />} */}
                {/* /> */}
              </Routes>
            </Box>
          </Box>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

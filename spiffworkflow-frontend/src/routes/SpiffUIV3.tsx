import React, { useState, useEffect, ReactElement } from 'react';
import {
  Box,
  Container,
  CssBaseline,
  Grid,
  ThemeProvider,
  createTheme,
} from '@mui/material';
import { Route, Routes, useLocation } from 'react-router';
import { createSpiffTheme } from '../a-spiffui-v3/assets/theme/SpiffTheme';
import Homepage from '../a-spiffui-v3/views/Homepage';
import StartProcess from '../a-spiffui-v3/views/StartProcess/StartProcess';
import StartProcessInstance from '../a-spiffui-v3/views/StartProcess/StartProcessInstance';
import SideNav from '../a-spiffui-v3/components/SideNav';
import LoginHandler from '../components/LoginHandler';
import Login from './Login';

const fadeIn = 'fadeIn';
const fadeOutImmediate = 'fadeOutImmediate';

export default function SpiffUIV3() {
  const [globalTheme, setGlobalTheme] = useState(
    createTheme(createSpiffTheme('light')),
  );
  const isDark = globalTheme.palette.mode === 'dark';
  const location = useLocation();

  const [displayLocation, setDisplayLocation] = useState(location);
  const [transitionStage, setTransistionStage] = useState('fadeIn');
  const [additionalNavElement, setAdditionalNavElement] =
    useState<ReactElement | null>(null);

  const [isNavCollapsed, setIsNavCollapsed] = useState<boolean>(false);

  const toggleNavCollapse = () => {
    setIsNavCollapsed(!isNavCollapsed);
  };

  const toggleDarkMode = () => {
    setGlobalTheme(createTheme(createSpiffTheme(isDark ? 'light' : 'dark')));
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

  /** Respond to transition events, this softens screen changes (UX) */
  useEffect(() => {
    if (location !== displayLocation) {
      setTransistionStage(fadeOutImmediate);
    }
  }, [location, displayLocation]);

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
            backgroundColor: isDark
              ? 'background.paper'
              : 'background.mediumlight',
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
            <SideNav
              isCollapsed={isNavCollapsed}
              onToggleCollapse={toggleNavCollapse}
              onToggleDarkMode={toggleDarkMode}
              isDark={isDark}
              additionalNavElement={additionalNavElement}
              setAdditionalNavElement={setAdditionalNavElement}
            />
            <Box
              className={`${transitionStage}`}
              sx={{
                bgcolor: isDark ? 'background.paper' : 'background.light',
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
                <Route path="/" element={<Homepage />} />
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
              </Routes>
            </Box>
          </Box>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

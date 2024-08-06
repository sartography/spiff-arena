import React, { useState, useEffect, ReactElement } from 'react';
import {
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Container,
  CssBaseline,
  Grid,
} from '@mui/material';
import {
  Home,
  Add,
  Person,
  ChevronLeft,
  ChevronRight,
  Brightness4,
  Brightness7,
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Route, Routes, useLocation, useNavigate } from 'react-router';
import { createSpiffTheme } from '../a-spiffui-v2/assets/theme/SpiffTheme';
import Homepage from '../a-spiffui-v3/views/Homepage';
import SpiffLogo from '../a-spiffui-v2/components/SpiffLogo';
import SpiffTooltip from '../components/SpiffTooltip';
import StartProcess from '../a-spiffui-v2/views/StartProcess/StartProcess';

const drawerWidth = 350;
const collapsedDrawerWidth = 64;
const mainBlue = 'primary.main';

type OwnProps = {
  isCollapsed: boolean;
  onToggleCollapse: Function;
  onToggleDarkMode: Function;
  isDark: boolean;
  additionalNavElement?: ReactElement | null;
  setAdditionalNavElement: Function;
};

function SideNav({
  isCollapsed,
  onToggleCollapse,
  onToggleDarkMode,
  isDark,
  additionalNavElement,
  setAdditionalNavElement,
}: OwnProps) {
  const navigate = useNavigate();
  const location = useLocation();
  const selectedBackgroundColor = isDark
    ? 'rgba(255, 255, 255, 0.16)'
    : '#F0F9FF';

  let selectedTab = 0;
  if (location.pathname === '/newuiv3/startprocess') {
    selectedTab = 1;
  }

  return (
    <Box
      sx={{
        width: isCollapsed ? collapsedDrawerWidth : drawerWidth,
        flexShrink: 0,
        borderRight: '1px solid #e0e0e0',
        height: '100vh',
        bgcolor: isDark ? 'background.paper' : 'background.mediumlight',
        transition: 'width 0.3s',
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      <Box
        sx={{
          p: 2,
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        {!isCollapsed && (
          <Typography
            variant="h6"
            color={mainBlue}
            sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center' }}
          >
            <SpiffLogo />
          </Typography>
        )}
        <IconButton
          onClick={onToggleCollapse}
          sx={{ ml: isCollapsed ? 'auto' : 0 }}
        >
          {isCollapsed ? <ChevronRight /> : <ChevronLeft />}
        </IconButton>
      </Box>
      <List>
        {[
          { text: 'HOME', icon: <Home /> },
          { text: 'START NEW PROCESS', icon: <Add /> },
        ].map((item, index) => (
          <ListItem
            button
            key={item.text}
            onClick={() => {
              setAdditionalNavElement(null);
              if (index === 0) {
                navigate('/newuiv3/homepage2');
              } else if (index === 1) {
                navigate('/newuiv3/startprocess');
              }
            }}
            sx={{
              bgcolor:
                selectedTab === index ? selectedBackgroundColor : 'inherit',
              color: selectedTab === index ? mainBlue : 'inherit',
              borderLeft:
                selectedTab === index
                  ? `4px solid ${mainBlue}`
                  : '4px solid transparent',
              '&:hover': {
                bgcolor: selectedBackgroundColor,
              },
              justifyContent: isCollapsed ? 'center' : 'flex-start',
            }}
          >
            <Tooltip title={isCollapsed ? item.text : ''} placement="right">
              <ListItemIcon
                sx={{ color: 'inherit', minWidth: isCollapsed ? 24 : 40 }}
              >
                {item.icon}
              </ListItemIcon>
            </Tooltip>
            {!isCollapsed && (
              <ListItemText
                primary={item.text}
                primaryTypographyProps={{
                  fontSize: '0.875rem',
                  fontWeight: selectedTab === index ? 'bold' : 'normal',
                }}
              />
            )}
          </ListItem>
        ))}
      </List>
      {!isCollapsed && <Box>{additionalNavElement}</Box>}
      <Box
        sx={{
          position: 'absolute',
          bottom: 16,
          left: isCollapsed ? '50%' : 16,
          transform: isCollapsed ? 'translateX(-50%)' : 'none',
          display: 'flex',
          flexDirection: isCollapsed ? 'column' : 'row',
          alignItems: 'center',
        }}
      >
        <SpiffTooltip title="Toggle dark mode">
          <IconButton onClick={onToggleDarkMode}>
            {isDark ? <Brightness7 /> : <Brightness4 />}
          </IconButton>
        </SpiffTooltip>
        <IconButton
          onClick={() => {
            /* Add appropriate onClick handler if needed */
          }}
        >
          <Person />
        </IconButton>
      </Box>
    </Box>
  );
}

/**
 * This is the main entry point for the new SpiffUI V2.
 * It's a full screen app that will be rendered on top of the old SpiffUI.
 * To access, use the root domain (e.g. localhost:7001) and add"/newui"
 */
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
                bgcolor: isDark ? 'background.default' : 'white', // Adjust background color based on theme
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
                <Route path="/homepage2" element={<Homepage />} />
                <Route
                  path="/startprocess"
                  element={
                    <StartProcess
                      setNavElementCallback={setAdditionalNavElement}
                    />
                  }
                />
              </Routes>
            </Box>
          </Box>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

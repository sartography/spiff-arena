import React, {
  useState,
  useEffect,
  ReactElement,
  MouseEventHandler,
} from 'react';
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
  ChevronLeft,
  ChevronRight,
  Logout,
} from '@mui/icons-material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { Route, Routes, useLocation, useNavigate } from 'react-router';
import { Link } from 'react-router-dom';
import { createSpiffTheme } from '../a-spiffui-v3/assets/theme/SpiffTheme';
import Homepage from '../a-spiffui-v3/views/Homepage';
import SpiffLogo from '../a-spiffui-v3/components/SpiffLogo';
import StartProcess from '../a-spiffui-v3/views/StartProcess/StartProcess';
import StartProcessInstance from '../a-spiffui-v3/views/StartProcess/StartProcessInstance';
import UserService from '../services/UserService';
import appVersionInfo from '../helpers/appVersionInfo';
import { DOCUMENTATION_URL } from '../config';

const drawerWidth = 350;
const collapsedDrawerWidth = 64;
const mainBlue = 'primary.main';

type OwnProps = {
  isCollapsed: boolean;
  onToggleCollapse: MouseEventHandler<HTMLButtonElement>;
  onToggleDarkMode: MouseEventHandler<HTMLButtonElement>;
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
  if (location.pathname === '/newui/startprocess') {
    selectedTab = 1;
  }

  const versionInfo = appVersionInfo();
  let aboutLinkElement = null;
  if (Object.keys(versionInfo).length) {
    aboutLinkElement = <Link to="/about">About</Link>;
  }
  const userEmail = UserService.getUserEmail();
  const username = UserService.getPreferredUsername();
  let externalDocumentationUrl = 'https://spiff-arena.readthedocs.io';
  if (DOCUMENTATION_URL) {
    externalDocumentationUrl = DOCUMENTATION_URL;
  }

  // 45 * number of nav items like "HOME" and "START NEW PROCESS" plus 140
  const pixelsToRemoveFromAdditionalElement = 45 * 2 + 140;

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
                navigate('/newui');
              } else if (index === 1) {
                navigate('/newui/startprocess');
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
      {!isCollapsed && (
        <Box
          sx={{
            width: '100%',
            height: `calc(100vh - ${pixelsToRemoveFromAdditionalElement}px)`,
          }}
        >
          {additionalNavElement}
        </Box>
      )}
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
        <div style={{ display: 'flex' }} id="user-profile-toggletip">
          <Tooltip title="User Actions" arrow placement="bottom-start">
            <IconButton
              aria-label="User Actions"
              className="user-profile-toggletip-button"
            >
              <div className="user-circle">{username[0].toUpperCase()}</div>
            </IconButton>
          </Tooltip>
          <div className="user-profile-toggletip-content">
            <p>
              <strong>{username}</strong>
            </p>
            {username !== userEmail && <p>{userEmail}</p>}
            <hr />
            {aboutLinkElement}
            <a target="_blank" href={externalDocumentationUrl} rel="noreferrer">
              Documentation
            </a>
            {/* <ExtensionUxElementForDisplay */}
            {/*   displayLocation="user_profile_item" */}
            {/*   elementCallback={extensionUserProfileElement} */}
            {/*   extensionUxElements={extensionUxElements} */}
            {/* /> */}
            {!UserService.authenticationDisabled() ? (
              <>
                <hr />
                <IconButton
                  data-qa="logout-button"
                  className="button-link"
                  onClick={() => console.log('WE LOG OUT')}
                >
                  <Logout />
                </IconButton>
              </>
            ) : null}
          </div>
        </div>
        {/* <SpiffTooltip title="Toggle dark mode"> */}
        {/*   <IconButton onClick={onToggleDarkMode}> */}
        {/*     {isDark ? <Brightness7 /> : <Brightness4 />} */}
        {/*   </IconButton> */}
        {/* </SpiffTooltip> */}
        {/* <SpiffTooltip title="Logout"> */}
        {/*   <IconButton */}
        {/*     onClick={() => { */}
        {/*     }} */}
        {/*   > */}
        {/*     <Person /> */}
        {/*   </IconButton> */}
        {/* </SpiffTooltip> */}
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
              </Routes>
            </Box>
          </Box>
        </Grid>
      </Container>
    </ThemeProvider>
  );
}

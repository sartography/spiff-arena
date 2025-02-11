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
  Paper,
  Link as MuiLink,
  useMediaQuery,
} from '@mui/material';
import {
  Home,
  Add,
  ChevronLeft,
  ChevronRight,
  Logout,
  Person,
  Brightness7,
  Brightness4,
  Close as CloseIcon,
  Schema,
  Timeline,
  Storage,
  Markunread,
  SettingsApplicationsSharp,
} from '@mui/icons-material';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import appVersionInfo from '../../helpers/appVersionInfo';
import { DOCUMENTATION_URL } from '../../config';
import UserService from '../../services/UserService';
import SpiffLogo from './SpiffLogo';
import SpiffTooltip from './SpiffTooltip';

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

// Define an object to map route paths to identifiers
const routeIdentifiers = {
  HOME: 'home',
  START_NEW_PROCESS: 'startNewProcess',
  PROCESSES: 'processes',
  PROCESS_INSTANCES: 'processInstances',
  DATA_STORES: 'dataStores',
  MESSAGES: 'messages',
  CONFIGURATION: 'configuration',
};

// eslint-disable-next-line sonarjs/cognitive-complexity
function SideNav({
  isCollapsed,
  onToggleCollapse,
  onToggleDarkMode,
  isDark,
  additionalNavElement,
  setAdditionalNavElement,
}: OwnProps) {
  const navigate = useNavigate();
  const isMobile = useMediaQuery((theme: any) => theme.breakpoints.down('sm'));

  const location = useLocation();

  // Determine the selected tab based on the current route
  let selectedTab = null;
  if (location.pathname === '/newui') {
    selectedTab = routeIdentifiers.HOME;
  } else if (location.pathname === '/newui/startprocess') {
    selectedTab = routeIdentifiers.START_NEW_PROCESS;
  } else if (location.pathname.startsWith('/newui/process-instances')) {
    selectedTab = routeIdentifiers.PROCESS_INSTANCES;
  } else if (location.pathname.startsWith('/newui/process-')) {
    selectedTab = routeIdentifiers.PROCESSES; // This might need further refinement
  } else if (location.pathname === '/newui/data-stores') {
    selectedTab = routeIdentifiers.DATA_STORES;
  } else if (location.pathname === '/newui/messages') {
    selectedTab = routeIdentifiers.MESSAGES;
  } else if (location.pathname.startsWith('/newui/configuration')) {
    selectedTab = routeIdentifiers.CONFIGURATION;
  }

  const versionInfo = appVersionInfo();
  let aboutLinkElement = null;
  if (Object.keys(versionInfo).length) {
    aboutLinkElement = (
      <MuiLink component={Link} to="/newui/about">
        About
      </MuiLink>
    );
  }
  const userEmail = UserService.getUserEmail();
  const username = UserService.getPreferredUsername();
  let externalDocumentationUrl = 'https://spiff-arena.readthedocs.io';
  if (DOCUMENTATION_URL) {
    externalDocumentationUrl = DOCUMENTATION_URL;
  }

  // State for controlling the display of the user profile section
  const [showUserProfile, setShowUserProfile] = useState(false);

  const handlePersonIconClick = () => {
    setShowUserProfile(!showUserProfile);
  };

  // Close user profile section when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const element = event.target as HTMLElement;
      if (
        element &&
        !element.closest('.user-profile') &&
        !element.closest('.person-icon')
      ) {
        setShowUserProfile(false);
      }
    };

    window.addEventListener('click', handleClickOutside);

    return () => {
      window.removeEventListener('click', handleClickOutside);
    };
  }, []);

  // 45 * number of nav items like "HOME" and "START NEW PROCESS" plus 140
  const pixelsToRemoveFromAdditionalElement = 45 * 2 + 140;

  const collapseOrExpandIcon = isCollapsed ? <ChevronRight /> : <ChevronLeft />;

  const navItems = [
    {
      text: 'HOME',
      icon: <Home />,
      route: '/newui',
      id: routeIdentifiers.HOME,
    },
    {
      text: 'START NEW PROCESS',
      icon: <Add />,
      route: '/newui/startprocess',
      id: routeIdentifiers.START_NEW_PROCESS,
    },
    {
      text: 'PROCESSES',
      icon: <Schema />,
      route: '/newui/process-groups',
      id: routeIdentifiers.PROCESSES,
    },
    {
      text: 'PROCESS INSTANCES',
      icon: <Timeline />,
      route: '/newui/process-instances',
      id: routeIdentifiers.PROCESS_INSTANCES,
    },
    {
      text: 'DATA STORES',
      icon: <Storage />,
      route: '/newui/data-stores',
      id: routeIdentifiers.DATA_STORES,
    },
    {
      text: 'MESSAGES',
      icon: <Markunread />,
      route: '/newui/messages',
      id: routeIdentifiers.MESSAGES,
    },
    {
      text: 'CONFIGURATION',
      icon: <SettingsApplicationsSharp />,
      route: '/newui/configuration',
      id: routeIdentifiers.CONFIGURATION,
    },
  ];

  return (
    <>
      <Box
        sx={{
          width: isCollapsed ? collapsedDrawerWidth : drawerWidth,
          flexShrink: 0,
          borderRight: '1px solid #e0e0e0',
          height: '100vh',
          bgcolor: 'background.nav',
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
              <MuiLink component={Link} to="/newui">
                <SpiffLogo />
              </MuiLink>
            </Typography>
          )}
          <IconButton
            onClick={(event) => {
              onToggleCollapse(event);
            }}
            sx={{ ml: isCollapsed ? 'auto' : 0 }}
          >
            {isMobile ? <CloseIcon /> : collapseOrExpandIcon}
          </IconButton>{' '}
        </Box>
        <List>
          {navItems.map((item) => (
            <ListItem
              component={Link} // Use Link component
              to={item.route}   // Set the target route
              key={item.text}
              onClick={() => {
                setAdditionalNavElement(null);
              }}
              sx={{
                bgcolor:
                  selectedTab === item.id ? 'background.light' : 'inherit',
                color: selectedTab === item.id ? mainBlue : 'inherit',
                borderColor: selectedTab === item.id ? mainBlue : 'transparent',
                borderLeftWidth: '4px',
                borderStyle: 'solid',
                justifyContent: isCollapsed ? 'center' : 'flex-start',
                '&:hover': {
                  cursor: 'pointer', // Add pointer cursor on hover
                },
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
                  data-qa={`nav-${item.text.toLowerCase().replace(' ', '-')}`}
                  primaryTypographyProps={{
                    fontSize: '0.875rem',
                    fontWeight: selectedTab === item.id ? 'bold' : 'normal',
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
            alignItems: isCollapsed ? 'center' : 'flex-start',
            display: 'flex',
            flexDirection: isCollapsed ? 'column' : 'row',
            gap: isCollapsed ? 0 : 1,
          }}
        >
          <SpiffTooltip
            title="User Actions"
            placement={isCollapsed ? 'right' : 'top'}
          >
            <IconButton
              aria-label="User Actions"
              onClick={handlePersonIconClick}
              className="person-icon"
            >
              <Person />
            </IconButton>
          </SpiffTooltip>
          <SpiffTooltip
            title="Toggle dark mode"
            placement={isCollapsed ? 'right' : 'top'}
          >
            <IconButton onClick={onToggleDarkMode}>
              {isDark ? <Brightness7 /> : <Brightness4 />}
            </IconButton>
          </SpiffTooltip>
          <SpiffTooltip
            title="Switch to Classic UI"
            placement={isCollapsed ? 'right' : 'top'}
          >
            <IconButton aria-label="Switch Site" onClick={() => navigate('/')}>
              <Home />
            </IconButton>
          </SpiffTooltip>
        </Box>
      </Box>
      {showUserProfile && (
        <Paper
          elevation={3}
          className="user-profile"
          sx={{
            position: 'fixed',
            bottom: isCollapsed ? 100 : 60, // if it's collapsed, make it a little higher so it doesn't overlap with the tooltip to the right of the icon
            left: 64,
            right: 'auto',
            width: 256,
            padding: 2,
            zIndex: 1300,
            bgcolor: 'background.paper',
          }}
        >
          <Typography variant="subtitle1">{username}</Typography>
          {username !== userEmail && (
            <Typography variant="body2">{userEmail}</Typography>
          )}
          <hr />
          {aboutLinkElement}
          <br />
          <MuiLink
            component="a"
            href={externalDocumentationUrl}
            target="_blank"
            rel="noreferrer"
          >
            Documentation
          </MuiLink>
          {!UserService.authenticationDisabled() && (
            <>
              <hr />
              <MuiLink
                component="button"
                onClick={() => UserService.doLogout()}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  textDecoration: 'none',
                  color: 'inherit',
                }}
              >
                <Logout />
                &nbsp;&nbsp;Sign out
              </MuiLink>
            </>
          )}
        </Paper>
      )}
    </>
  );
}

export default SideNav;

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
} from '@mui/icons-material';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import appVersionInfo from '../../helpers/appVersionInfo';
import { DOCUMENTATION_URL } from '../../config';
import UserService from '../../services/UserService';
import SpiffLogo from './SpiffLogo';
import SpiffTooltip from '../../components/SpiffTooltip';

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
    aboutLinkElement = (
      <MuiLink component={Link} to="/about">
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

  return (
    <>
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
            alignItems: isCollapsed ? 'center' : 'flex-start',
            display: 'flex',
            flexDirection: isCollapsed ? 'column' : 'row',
            alignItems: 'center',
            gap: isCollapsed ? 0 : 1,
          }}
        >
          <Tooltip title="User Actions" arrow placement="top">
            <IconButton
              aria-label="User Actions"
              onClick={handlePersonIconClick}
              className="person-icon"
            >
              <Person />
            </IconButton>
          </Tooltip>
          <SpiffTooltip title="Toggle dark mode">
            <IconButton onClick={onToggleDarkMode}>
              {isDark ? <Brightness7 /> : <Brightness4 />}
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
            bottom: 60,
            left: isCollapsed ? '50%' : 80,
            transform: isCollapsed ? 'translateX(-50%)' : 'none',
            width: isCollapsed ? 'calc(100% - 32px)' : 256,
            padding: 2,
            zIndex: 1300,
            bgcolor: isDark ? 'background.paper' : 'background.default',
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

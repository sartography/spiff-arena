import {
  Box,
  Paper,
  SpeedDial,
  SpeedDialAction,
  SpeedDialIcon,
  Stack,
  useTheme,
} from '@mui/material';
import PersonOutline from '@mui/icons-material/PersonOutline';
import Moon from '@mui/icons-material/DarkModeOutlined';
import Lightbulb from '@mui/icons-material/LightbulbOutlined';
import Logout from '@mui/icons-material/LogoutOutlined';
import { grey } from '@mui/material/colors';
import { Subject } from 'rxjs';
import SpiffLogo from '../../../components/SpiffLogo';
import MenuItem, { MenuItemData } from './MenuItem';
import UserService from '../../../../services/UserService';

/**
 * MenuBar running along top of app.
 * TODO: Check responsivness, and speedial may be replaced by hamburger
 */
export default function TopMenu({
  callback,
}: {
  callback: (data: MenuItemData) => void;
}) {
  /** Broadcasts to all MenuItems so they can update selected styles etc.  */
  const menuItemStream = new Subject<MenuItemData>();
  const menuItemWidth = 150;

  const iconColor =
    useTheme().palette.mode === 'light' ? grey[600] : 'primary.light';

  const navMenuItemData: MenuItemData[] = [
    {
      text: 'Dashboard',
      path: '/newui/dashboard',
    },
    {
      text: 'Start a Process',
      path: '/newui/startprocess',
    },
  ];

  const userMenuItemData: MenuItemData[] = [
    {
      text: 'Dark Mode',
      icon: <Moon sx={{ color: iconColor }} />,
      path: '',
      toggleData: {
        toggled: false,
        toggleIcon: <Lightbulb />,
        toggleText: 'Light Mode',
      },
    },
    { text: 'Logout', icon: <Logout sx={{ color: iconColor }} />, path: '' },
    {
      text: UserService.getPreferredUsername(),
      icon: <PersonOutline sx={{ color: iconColor }} />,
      path: '',
    },
  ];

  const handleMenuItemClick = (item: MenuItemData) => {
    // Broadcast to all MenuItems so they can update selected styles etc.
    menuItemStream.next(item);
    callback(item);
  };

  const handleSpeedDialAction = (item: MenuItemData) => {
    callback(item);
  };

  return (
    <Paper
      elevation={0}
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        paddingLeft: 3,
        paddingRight: 3,
        paddingTop: 2,
        paddingBottom: 2,
        borderBottom: 1,
        borderBottomColor: 'divider',
        borderBottomStyle: 'solid',
      }}
    >
      <Stack
        direction="row"
        sx={{
          width: '100%',
          gap: 2,
        }}
      >
        <Box sx={{ paddingTop: 1 }}>
          <SpiffLogo />
        </Box>
        <Box sx={{ width: { xs: 0, md: 32 } }} />
        <Stack direction="row" gap={3} sx={{ width: '100%' }}>
          {navMenuItemData.map((item) => (
            <Box sx={{ width: menuItemWidth }}>
              <MenuItem
                data={item}
                callback={() => handleMenuItemClick(item)}
                stream={menuItemStream}
              />
            </Box>
          ))}
        </Stack>
        <Stack
          direction="row"
          sx={{
            gap: 2,
            width: '100%',
            justifyContent: 'right',
            display: { xs: 'none', md: 'flex' },
          }}
        >
          {userMenuItemData.map((item) => (
            <Box sx={{ width: menuItemWidth }}>
              <MenuItem
                data={item}
                key={item.text}
                callback={callback}
                stream={menuItemStream}
              />
            </Box>
          ))}
        </Stack>
        <Box
          sx={{ display: { xs: 'block', md: 'none' }, position: 'relative' }}
        >
          <SpeedDial
            color="secondary"
            sx={{
              position: 'absolute',
              right: -10,
              top: -9,
            }}
            direction="down"
            ariaLabel="SpeedDial basic example"
            icon={<SpeedDialIcon />}
          >
            {userMenuItemData.map((item) => (
              <SpeedDialAction
                key={item.text}
                icon={item.icon}
                tooltipTitle={item.text}
                onClick={() => handleSpeedDialAction(item)}
                FabProps={{ color: 'warning' }}
              />
            ))}
          </SpeedDial>
        </Box>
      </Stack>
    </Paper>
  );
}

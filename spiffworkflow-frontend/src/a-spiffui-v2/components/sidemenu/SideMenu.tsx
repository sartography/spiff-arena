import { Box, Stack } from '@mui/material';
import PersonOutline from '@mui/icons-material/PersonOutline';
import SpiffLogo from '../SpiffLogo';
import MenuItem, { MenuItemData } from './MenuItem';
import HomeLine from '../../assets/icons/home-line.svg';
import Route from '../../assets/icons/route.svg';
import Config from '../../assets/icons/configuration.svg';
import CheckSquare from '../../assets/icons/check-square.svg';
import Mail from '../../assets/icons/mail.svg';
import DataBase from '../../assets/icons/database.svg';
import Settings from '../../assets/icons/settings.svg';
import Moon from '../../assets/icons/moon.svg';
import Logout from '../../assets/icons/logout.svg';
import UserService from '../../../services/UserService';

/**
 * SideMenu component that satisfies design requirements.
 * Very basic click 'n handle sort of thing.
 */
export default function SideMenu() {
  const navMenuItemData = [
    { label: 'Dashboard', icon: <HomeLine />, path: '/' },
    { label: 'Processes', icon: <Route />, path: '/' },
    { label: 'Task List', icon: <CheckSquare />, path: '/' },
    { label: 'Messages', icon: <Mail />, path: '/' },
    { label: 'Data Stores', icon: <DataBase />, path: '/' },
    { label: 'Configuration', icon: <Config />, path: '/' },
    { label: 'Settings', icon: <Settings />, path: '/' },
  ];

  /** Using UserService to grab and display userName */
  const userMenuItemData = [
    { label: 'Dark Mode', icon: <Moon />, path: '/' },
    { label: 'Logout', icon: <Logout />, path: '/' },
    {
      label: UserService.getPreferredUsername(),
      icon: <PersonOutline />,
      path: '/',
    },
  ];

  const handleMenuItemClick = (data: MenuItemData) => {
    console.log(data);
  };

  return (
    <Stack padding={2} gap={2} height="100%">
      <Stack height="100%">
        <Box width="85%">
          <SpiffLogo />
        </Box>
        <Stack gap={2} padding={1}>
          {navMenuItemData.map((item) => (
            <MenuItem
              data={item}
              key={item.label}
              callback={handleMenuItemClick}
            />
          ))}
        </Stack>
      </Stack>
      <Stack height={275} gap={2} padding={2}>
        {userMenuItemData.map((item) => (
          <MenuItem
            data={item}
            key={item.label}
            callback={handleMenuItemClick}
          />
        ))}
      </Stack>
    </Stack>
  );
}

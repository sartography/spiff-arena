import { Box, Stack } from '@mui/material';
import PersonOutline from '@mui/icons-material/PersonOutline';
import HomeLine from '@mui/icons-material/HomeOutlined';
import Route from '@mui/icons-material/RouteOutlined';
import Config from '@mui/icons-material/TuneOutlined';
import CheckSquare from '@mui/icons-material/CheckBoxOutlined';
import Mail from '@mui/icons-material/EmailOutlined';
import DataBase from '@mui/icons-material/StorageOutlined';
import Moon from '@mui/icons-material/DarkModeOutlined';
import Lightbulb from '@mui/icons-material/LightbulbOutlined';
import Settings from '@mui/icons-material/SettingsOutlined';
import Logout from '@mui/icons-material/LogoutOutlined';
import SpiffLogo from '../SpiffLogo';
import MenuItem, { MenuItemData } from './MenuItem';
import UserService from '../../../services/UserService';

/**
 * SideMenu component that satisfies design requirements.
 * Very basic click 'n handle sort of thing.
 */
export default function SideMenu({
  callback,
}: {
  callback: (data: MenuItemData) => void;
}) {
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

  return (
    <Stack padding={2} gap={2}>
      <Stack>
        <Box width="85%">
          <SpiffLogo />
        </Box>
        <Stack gap={2} padding={1}>
          {navMenuItemData.map((item) => (
            <MenuItem data={item} key={item.label} callback={callback} />
          ))}
        </Stack>
      </Stack>
      {/**
       * This stack is absolute positioned to make it bottom-sticky.
       * Constrain the width to prevent it from taking up the whole screen.
       */}
      <Stack
        gap={2}
        padding={1}
        sx={{ position: 'absolute', width: 210, bottom: 0 }}
      >
        {userMenuItemData.map((item) => (
          <MenuItem data={item} key={item.label} callback={callback} />
        ))}
      </Stack>
    </Stack>
  );
}

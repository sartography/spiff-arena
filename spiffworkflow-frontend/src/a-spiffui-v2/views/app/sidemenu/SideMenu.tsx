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
import SpiffLogo from '../../../components/SpiffLogo';
import MenuItem, { MenuItemData } from './MenuItem';
import UserService from '../../../../services/UserService';
import SpiffIcon from '../../../assets/icons/spiff-icon.svg';

/**
 * SideMenu component that satisfies design requirements.
 * Very basic click 'n handle sort of thing.
 */
export default function SideMenu({
  callback,
  collapsed,
}: {
  callback: (data: MenuItemData) => void;
  collapsed: boolean;
}) {
  /** Top set of app nav items */
  const navMenuItemData: MenuItemData[] = [
    { text: 'Dashboard', icon: <HomeLine />, path: '/' },
    { text: 'Processes', icon: <Route />, path: '/' },
    { text: 'Task List', icon: <CheckSquare />, path: '/' },
    { text: 'Messages', icon: <Mail />, path: '/' },
    { text: 'Data Stores', icon: <DataBase />, path: '/' },
    { text: 'Configuration', icon: <Config />, path: '/' },
    { text: 'Settings', icon: <Settings />, path: '/' },
  ];

  /** Bottom set of user nav items, displaying name etc. */
  const userMenuItemData: MenuItemData[] = [
    {
      text: 'Dark Mode',
      icon: <Moon />,
      path: '/',
      toggleData: {
        toggled: false,
        toggleIcon: <Lightbulb />,
        toggleText: 'Light Mode',
      },
    },
    { text: 'Logout', icon: <Logout />, path: '/' },
    {
      text: UserService.getPreferredUsername(),
      icon: <PersonOutline />,
      path: '/',
    },
  ];

  return (
    <Stack
      gap={2}
      sx={{
        height: '100vh',
        width: collapsed ? 45 : { xs: 0, sm: 45, md: 240 },
        overflow: 'hidden',
      }}
    >
      <Stack>
        <Box width="85%">
          {collapsed ? (
            <Box sx={{ paddingTop: 2 }}>
              <SpiffIcon />
            </Box>
          ) : (
            <SpiffLogo />
          )}
        </Box>
        <Stack gap={2}>
          {navMenuItemData.map((item) => (
            <MenuItem data={item} key={item.text} callback={callback} />
          ))}
        </Stack>
      </Stack>
      {/**
       * This stack is absolute positioned to make it bottom-sticky.
       * Constrain the width to prevent it from taking up the whole screen.
       */}
      <Stack gap={2} direction="column" padding={1} sx={{ marginTop: 'auto' }}>
        {userMenuItemData.map((item) => (
          <MenuItem data={item} key={item.text} callback={callback} />
        ))}
      </Stack>
    </Stack>
  );
}

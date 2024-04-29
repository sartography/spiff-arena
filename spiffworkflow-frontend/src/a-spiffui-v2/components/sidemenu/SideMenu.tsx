import { Box, Stack } from '@mui/material';
import PersonOutline from '@mui/icons-material/PersonOutline';
import SpiffLogo from '../SpiffLogo';
import MenuItem from '../MenuItem';
import HomeLine from '../../assets/icons/home-line.svg';
import Route from '../../assets/icons/route.svg';
import Config from '../../assets/icons/configuration.svg';
import CheckSquare from '../../assets/icons/check-square.svg';
import Mail from '../../assets/icons/mail.svg';
import DataBase from '../../assets/icons/database.svg';
import Settings from '../../assets/icons/settings.svg';
import Moon from '../../assets/icons/moon.svg';
import Logout from '../../assets/icons/logout.svg';

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

  const userMenuItemData = [
    { label: 'Dark Mode', icon: <Moon />, path: '/' },
    { label: 'Logout', icon: <Logout />, path: '/' },
    { label: 'Happy User', icon: <PersonOutline />, path: '/' },
  ];

  return (
    <Stack width={240} padding={2} gap={2} height="100%">
      <Stack height="inherit">
        <Box width="85%">
          <SpiffLogo />
        </Box>
        <Stack gap={5} padding={2}>
          {navMenuItemData.map((item) => (
            <MenuItem data={item} key={item.label} />
          ))}
        </Stack>
      </Stack>
      <Stack height={275} gap={5} padding={2}>
        {userMenuItemData.map((item) => (
          <MenuItem data={item} key={item.label} />
        ))}
      </Stack>
    </Stack>
  );
}

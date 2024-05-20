import { Box, Paper, Stack, useTheme } from '@mui/material';
import PersonOutline from '@mui/icons-material/PersonOutline';
import HomeLine from '@mui/icons-material/HomeOutlined';
import Moon from '@mui/icons-material/DarkModeOutlined';
import Lightbulb from '@mui/icons-material/LightbulbOutlined';
import Logout from '@mui/icons-material/LogoutOutlined';
import { grey } from '@mui/material/colors';
import SpiffLogo from '../../components/SpiffLogo';
import MenuItem, { MenuItemData } from '../app/sidemenu/MenuItem';
import UserService from '../../../services/UserService';

export default function TopMenu({
  callback,
}: {
  callback: (data: MenuItemData) => void;
}) {
  const iconColor = useTheme().palette.mode === 'light' ? grey[600] : grey[50];

  const navMenuItemData: MenuItemData[] = [
    { text: 'Home', icon: <HomeLine sx={{ color: iconColor }} />, path: '/' },
  ];

  const userMenuItemData: MenuItemData[] = [
    {
      text: 'Dark Mode',
      icon: <Moon sx={{ color: iconColor }} />,
      path: '/',
      toggleData: {
        toggled: false,
        toggleIcon: <Lightbulb />,
        toggleText: 'Light Mode',
      },
    },
    { text: 'Logout', icon: <Logout sx={{ color: iconColor }} />, path: '/' },
    {
      text: UserService.getPreferredUsername(),
      icon: <PersonOutline sx={{ color: iconColor }} />,
      path: '/',
    },
  ];
  return (
    <Paper
      elevation={1}
      sx={{
        width: '100%',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        paddingLeft: 3,
        paddingRight: 3,
        paddingTop: 2,
        paddingBottom: 1,
      }}
    >
      <Stack
        direction="row"
        sx={{
          width: '100%',
          gap: 2,
        }}
      >
        <SpiffLogo />
        <Box sx={{ width: 32 }} />
        {navMenuItemData.map((item) => (
          <MenuItem data={item} key={item.text} callback={callback} />
        ))}
        <Box
          sx={{
            width: '100%',
            display: 'flex',
            justifyContent: 'right',
          }}
        >
          {userMenuItemData.map((item) => (
            <MenuItem data={item} key={item.text} callback={callback} />
          ))}
        </Box>
      </Stack>
    </Paper>
  );
}

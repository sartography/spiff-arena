import {
  Box,
  Button,
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
import AddIcon from '@mui/icons-material/Add';
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
  const iconColor =
    useTheme().palette.mode === 'light' ? grey[600] : 'primary.light';

  const handleSpeedDialAction = (item: MenuItemData) => {
    console.log('>>>>>', item);
    callback(item);
  };

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
        paddingBottom: 2,
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
        <Box sx={{ width: '100%' }}>
          <Button
            title="Start New Process"
            variant="contained"
            startIcon={<AddIcon />}
            sx={{ width: 200, height: 40 }}
          >
            Start New Process
          </Button>
        </Box>
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
            <MenuItem data={item} key={item.text} callback={callback} />
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

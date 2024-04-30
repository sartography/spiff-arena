import { Stack, Typography, Button } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import NotificationBell from '../../assets/icons/notification-bell.svg';

export default function Toolbar() {
  const showTime = () => {
    return new Date().toDateString();
  };

  return (
    <Stack direction="row">
      <Stack width={210}>
        <Typography variant="h4">Dashboards</Typography>
        <Typography variant="caption">Last Updated: {showTime()}</Typography>
      </Stack>
      <Stack
        width="100%"
        direction="row"
        flexDirection="row-reverse"
        height={45}
        gap={3}
      >
        <NotificationBell />
        <Button title="Hello" variant="contained" startIcon={<AddIcon />}>
          Start New Process
        </Button>
      </Stack>
    </Stack>
  );
}

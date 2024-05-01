import { Stack, Typography, Button, Grid, Box } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import NotificationBell from '../../assets/icons/notification-bell.svg';

export default function Toolbar() {
  const showTime = () => {
    return new Date().toDateString();
  };

  return (
    <Grid container>
      <Grid item xs={2}>
        <Typography variant="h4">Dashboards</Typography>
        <Typography variant="caption" noWrap>
          Last Updated: {showTime()}
        </Typography>
      </Grid>
      <Grid item xs={12} sm={10}>
        <Box
          sx={{
            display: 'flex',
            justifyContent: { xs: '', sm: 'flex-end' },
            alignItems: 'center',
            height: '100%',
          }}
          gap={2}
        >
          <Button
            title="Hello"
            variant="contained"
            startIcon={<AddIcon />}
            sx={{ width: 200, height: 40 }}
          >
            Start New Process
          </Button>
          <NotificationBell />
        </Box>
      </Grid>
    </Grid>
  );
}
